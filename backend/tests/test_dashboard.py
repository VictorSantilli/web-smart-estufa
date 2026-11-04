from datetime import timedelta

import pytest

from app.services.thresholds import classify_humidity, classify_temperature


@pytest.fixture
def setup(make_user, make_greenhouse, login):
    g1, g2 = make_greenhouse("Estufa 01"), make_greenhouse("Estufa 02")
    make_user("admin@estufa.com", admin=True)
    make_user("a@estufa.com", greenhouses=(g1,))
    return {"g1": g1, "g2": g2, "admin": login("admin@estufa.com"), "a": login("a@estufa.com")}


def get(client, setup, greenhouse, who="a"):
    return client.get(f"/api/dashboard/{greenhouse.id}", headers=setup[who])


# ---------- faixas ----------


@pytest.mark.parametrize(
    ("value", "level"),
    [(15.9, "low"), (16, "ok"), (25, "ok"), (25.1, "warning"), (26, "warning"), (26.5, "critical")],
)
def test_temperature_levels(value, level):
    from app.core.config import get_settings

    assert classify_temperature(value, get_settings()) == level


@pytest.mark.parametrize(("value", "level"), [(64, "low"), (65, "ok"), (85, "ok"), (86, "warning")])
def test_humidity_levels(value, level):
    from app.core.config import get_settings

    assert classify_humidity(value, get_settings()) == level


# ---------- dashboard ----------


def test_no_data(client, setup):
    body = get(client, setup, setup["g1"]).json()
    assert body["has_data"] is False
    assert body["is_online"] is False
    assert body["last_reading_at"] is None
    assert body["canopy"]["temperature"]["value"] is None
    assert body["fans"]["state"] == "unknown"


def test_latest_reading_is_shown(client, setup, make_reading):
    make_reading(setup["g1"], minutes_ago=10, temp=20)
    make_reading(setup["g1"], minutes_ago=2, temp=25.5, hum=88, temp_ceiling=27, fans=True)
    body = get(client, setup, setup["g1"]).json()
    assert body["has_data"] is True
    assert body["is_online"] is True
    assert body["canopy"]["temperature"] == {
        "value": 25.5,
        "level": "warning",
        "measured_at": body["last_reading_at"],
        "is_current": True,
    }
    assert body["canopy"]["humidity"]["level"] == "warning"
    assert body["ceiling"]["temperature"]["level"] == "critical"
    assert body["fans"]["state"] == "on"
    assert body["thresholds"]["temp_critical"] == 26


def test_dates_are_utc_with_timezone(client, setup, make_reading):
    make_reading(setup["g1"], minutes_ago=1)
    body = get(client, setup, setup["g1"]).json()
    assert body["last_reading_at"].endswith("Z") or body["last_reading_at"].endswith("+00:00")


def test_last_communication_converts_brasilia_to_utc(client, setup, make_reading):
    """DataHoraGravacao está em Brasília (UTC-3); a API deve devolver em UTC."""
    reading = make_reading(setup["g1"], minutes_ago=5, delay_s=4)
    body = get(client, setup, setup["g1"]).json()
    from datetime import datetime

    sent = datetime.fromisoformat(body["last_reading_at"])
    comm = datetime.fromisoformat(body["last_communication_at"])
    assert timedelta(seconds=3) < comm - sent < timedelta(seconds=5)
    assert reading.data_hora_gravacao < reading.data_hora_envio  # no banco está "3h antes"


def test_offline_when_stale(client, setup, make_reading):
    make_reading(setup["g1"], minutes_ago=16)
    body = get(client, setup, setup["g1"]).json()
    assert body["has_data"] is True
    assert body["is_online"] is False
    assert body["stale_after_minutes"] == 15


def test_late_offline_queue_reading_counts_as_communication(client, setup, make_reading):
    """Leitura antiga que chegou agora (fila offline do ESP32): o sistema está online."""
    make_reading(setup["g1"], minutes_ago=120, delay_s=120 * 60 - 30)
    body = get(client, setup, setup["g1"]).json()
    assert body["is_online"] is True


def test_falls_back_to_send_time_without_recorded_time(client, setup, make_reading):
    make_reading(setup["g1"], minutes_ago=3, recorded=False)
    body = get(client, setup, setup["g1"]).json()
    assert body["last_communication_at"] == body["last_reading_at"]
    assert body["is_online"] is True


def test_failed_sensor_shows_last_valid_value(client, setup, make_reading):
    make_reading(setup["g1"], minutes_ago=10, temp=21, hum=70)
    make_reading(setup["g1"], minutes_ago=1, temp=None, hum=None)
    body = get(client, setup, setup["g1"]).json()
    canopy = body["canopy"]
    assert canopy["ok"] is False
    assert canopy["temperature"]["value"] == 21
    assert canopy["temperature"]["is_current"] is False
    assert canopy["temperature"]["measured_at"] != body["last_reading_at"]
    assert body["ceiling"]["ok"] is True


def test_fans_unknown_when_null(client, setup, make_reading):
    make_reading(setup["g1"], fans=None)
    assert get(client, setup, setup["g1"]).json()["fans"]["state"] == "unknown"
    make_reading(setup["g1"], minutes_ago=0.5, fans=False)
    assert get(client, setup, setup["g1"]).json()["fans"]["state"] == "off"


def test_reading_without_greenhouse_is_attributed_by_device(
    client, setup, make_reading, make_device
):
    make_device("esp32-01", setup["g1"])
    make_reading(None, device_id="esp32-01", temp=19)
    make_reading(None, device_id="esp32-desconhecido", minutes_ago=0.5, temp=30)
    body = get(client, setup, setup["g1"]).json()
    assert body["canopy"]["temperature"]["value"] == 19


def test_readings_from_other_greenhouse_are_not_mixed(client, setup, make_reading):
    make_reading(setup["g1"], minutes_ago=5, temp=20)
    make_reading(setup["g2"], minutes_ago=1, temp=30)
    assert get(client, setup, setup["g1"], "admin").json()["canopy"]["temperature"]["value"] == 20
    assert get(client, setup, setup["g2"], "admin").json()["canopy"]["temperature"]["value"] == 30


# ---------- permissões ----------


def test_common_user_cannot_see_other_greenhouse_dashboard(client, setup, make_reading):
    make_reading(setup["g2"])
    for path in (
        f"/api/dashboard/{setup['g2'].id}",
        f"/api/sensors/{setup['g2'].id}/latest",
        f"/api/greenhouses/{setup['g2'].id}/devices",
    ):
        response = client.get(path, headers=setup["a"])
        assert response.status_code == 404, path


def test_anonymous_cannot_see_dashboard(client, setup):
    assert client.get(f"/api/dashboard/{setup['g1'].id}").status_code == 401


# ---------- sensores e dispositivos ----------


def test_latest_raw_reading(client, setup, make_reading):
    assert (
        client.get(f"/api/sensors/{setup['g1'].id}/latest", headers=setup["a"]).status_code == 404
    )
    make_reading(setup["g1"], temp=22.5, fans=True)
    body = client.get(f"/api/sensors/{setup['g1'].id}/latest", headers=setup["a"]).json()
    assert body["canopy_temperature"] == 22.5
    assert body["fans_on"] is True
    assert body["device_id"] == "esp32-01"


def test_devices_with_last_contact(client, setup, make_reading, make_device):
    make_device("esp32-01", setup["g1"])
    make_device("esp32-02", setup["g1"])
    make_reading(setup["g1"], device_id="esp32-01", minutes_ago=2)
    body = client.get(f"/api/greenhouses/{setup['g1'].id}/devices", headers=setup["a"]).json()
    assert [(d["device_id"], d["is_online"]) for d in body] == [
        ("esp32-01", True),
        ("esp32-02", False),
    ]
    assert body[1]["last_reading_at"] is None
