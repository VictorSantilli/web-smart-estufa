from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.clock import utcnow
from app.core.errors import AppError
from app.models import LeituraSensor
from app.services.history_service import HistoryService


@pytest.fixture
def setup(make_user, make_greenhouse, make_device, login):
    g1, g2 = make_greenhouse("Estufa 01"), make_greenhouse("Estufa 02")
    make_device("esp32-01", g1)
    make_user("a@estufa.com", greenhouses=(g1,))
    make_user("b@estufa.com", greenhouses=(g2,))
    return {"g1": g1, "g2": g2, "a": login("a@estufa.com"), "b": login("b@estufa.com")}


@pytest.fixture
def add(db):
    """Grava uma leitura com DataHoraEnvio exato (UTC, sem tzinfo)."""

    def _add(sent_at, greenhouse=None, *, device="esp32-01", t=22, h=75, tt=24, ht=70):
        db.add(
            LeituraSensor(
                device_id=device,
                temperatura=t,
                umidade=h,
                temp_teto=tt,
                umid_teto=ht,
                data_hora_envio=sent_at,
                data_hora_gravacao=sent_at,
                id_estufa=greenhouse.id if greenhouse else None,
            )
        )
        db.commit()

    return _add


def get(client, setup, params="", who="a", greenhouse="g1"):
    return client.get(f"/api/history/{setup[greenhouse].id}{params}", headers=setup[who])


# ---------- 24 h ----------


def test_default_is_last_24h_raw(client, setup, add):
    now = utcnow()
    g1, g2 = setup["g1"], setup["g2"]
    add(now - timedelta(hours=25), g1, t=10)  # fora da janela
    add(now - timedelta(hours=2), g1, t=20)
    add(now - timedelta(hours=1), None, t=21)  # IdEstufa nulo: atribuída pelo DeviceId
    add(now - timedelta(minutes=30), g2, device="esp32-02", t=30)  # outra estufa
    add(now - timedelta(minutes=10), g1, t=23, h=None)

    response = get(client, setup)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["period"] == "24h"
    assert body["granularity"] == "raw"
    assert body["days"] == []
    assert [p["canopy_temperature"] for p in body["points"]] == [20, 21, 23]
    assert body["points"][-1]["canopy_humidity"] is None
    measured_at = body["points"][0]["measured_at"]
    assert measured_at.endswith("Z") or measured_at.endswith("+00:00")
    assert body["thresholds"]["temp_critical"] == 26


def test_raw_deduplicates_resent_readings(client, setup, add):
    sent = utcnow().replace(microsecond=0) - timedelta(hours=1)
    add(sent, setup["g1"], t=22, h=None)
    add(sent, setup["g1"], t=22, h=74)  # reenvio da fila offline, agora com umidade
    points = get(client, setup).json()["points"]
    assert len(points) == 1
    assert points[0]["canopy_humidity"] == 74


# ---------- agregados diários ----------


def test_7d_returns_every_day_with_gaps(client, setup, add):
    service_today = datetime.now(UTC).astimezone(ZoneInfo("America/Sao_Paulo")).date()
    # meio-dia local de ontem = 15h UTC
    yesterday_noon = datetime.combine(service_today - timedelta(days=1), datetime.min.time())
    yesterday_noon += timedelta(hours=15)
    add(yesterday_noon, setup["g1"], t=18, h=70, tt=None)
    add(yesterday_noon + timedelta(minutes=5), setup["g1"], t=22, h=80, tt=None)
    add(yesterday_noon + timedelta(minutes=10), setup["g1"], t=None, h=90, tt=None)

    body = get(client, setup, "?period=7d").json()
    assert body["granularity"] == "daily"
    assert body["points"] == []
    assert len(body["days"]) == 7
    assert body["days"][-1]["date"] == service_today.isoformat()

    by_date = {d["date"]: d for d in body["days"]}
    day = by_date[(service_today - timedelta(days=1)).isoformat()]
    assert day["samples"] == 3
    assert day["canopy_temperature"] == {"min": 18, "avg": 20, "max": 22}
    assert day["canopy_humidity"] == {"min": 70, "avg": 80, "max": 90}
    assert day["ceiling_temperature"] == {"min": None, "avg": None, "max": None}

    empty = by_date[(service_today - timedelta(days=3)).isoformat()]
    assert empty["samples"] == 0
    assert empty["canopy_temperature"]["avg"] is None


def test_30d_has_30_days(client, setup):
    assert len(get(client, setup, "?period=30d").json()["days"]) == 30


def test_daily_groups_by_local_day(db, setup, add):
    # 02:00 UTC de 10/03 ainda é 23:00 de 09/03 em Brasília.
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    add(datetime(2026, 3, 10, 2, 0), setup["g1"], t=19)
    add(datetime(2026, 3, 10, 4, 0), setup["g1"], t=25)
    result = HistoryService(db, now=now).history(setup["g1"], "7d", None, None)
    by_date = {d.date: d for d in result.days}
    assert by_date[date(2026, 3, 9)].canopy_temperature.max == 19
    assert by_date[date(2026, 3, 10)].canopy_temperature.max == 25
    assert result.start == datetime(2026, 3, 9, 3, 0, tzinfo=UTC)  # 00:00 local de 09/03


def test_daily_deduplicates(db, setup, add):
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    for _ in range(3):
        add(datetime(2026, 3, 14, 15, 0), setup["g1"], t=30)
    add(datetime(2026, 3, 14, 15, 5), setup["g1"], t=20)
    day = HistoryService(db, now=now).history(setup["g1"], "7d", None, None).days[-2]
    assert day.samples == 2
    assert day.canopy_temperature.avg == 25


# ---------- período personalizado ----------


def test_custom_short_range_is_raw(db, setup, add):
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    add(datetime(2026, 3, 10, 2, 59), setup["g1"], t=1)  # 23:59 de 09/03: fora
    add(datetime(2026, 3, 10, 3, 0), setup["g1"], t=2)  # 00:00 de 10/03: dentro
    add(datetime(2026, 3, 11, 2, 59), setup["g1"], t=3)  # 23:59 de 10/03: dentro
    add(datetime(2026, 3, 11, 3, 0), setup["g1"], t=4)  # 00:00 de 11/03: fora
    day = date(2026, 3, 10)
    result = HistoryService(db, now=now).history(setup["g1"], None, day, day)
    assert result.period == "custom"
    assert result.granularity == "raw"
    assert [p.canopy_temperature for p in result.points] == [2, 3]


def test_custom_long_range_is_daily(db, setup):
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    service = HistoryService(db, now=now)
    result = service.history(setup["g1"], None, date(2026, 1, 15), date(2026, 3, 15))
    assert result.granularity == "daily"
    assert len(result.days) == 60


@pytest.mark.parametrize(
    ("period", "start", "end", "code"),
    [
        (None, date(2026, 1, 14), date(2026, 3, 15), "range_too_long"),  # 61 dias
        (None, date(2026, 3, 10), date(2026, 3, 9), "invalid_range"),
        (None, date(2026, 3, 10), date(2026, 3, 16), "invalid_range"),  # futuro
        (None, date(2026, 3, 10), None, "invalid_range"),
        ("7d", date(2026, 3, 10), date(2026, 3, 11), "invalid_range"),
    ],
)
def test_custom_range_validation(db, setup, period, start, end, code):
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    with pytest.raises(AppError) as exc:
        HistoryService(db, now=now).history(setup["g1"], period, start, end)
    assert exc.value.status_code == 422
    assert exc.value.code == code


def test_custom_range_errors_via_api(client, setup):
    response = get(client, setup, "?start=2026-03-10&end=2026-03-01")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_range"
    assert get(client, setup, "?period=1y").status_code == 422
    assert get(client, setup, "?start=10-03-2026&end=2026-03-11").status_code == 422


# ---------- acesso ----------


def test_history_requires_access(client, setup):
    assert get(client, setup, who="b").status_code == 404
    assert client.get(f"/api/history/{setup['g1'].id}").status_code == 401
    assert client.get("/api/history/9999", headers=setup["a"]).status_code == 404
