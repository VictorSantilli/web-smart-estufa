from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import get_settings
from app.models import Deteccao, Estufa
from app.storage import blob_store
from app.storage.blob_store import IMAGE_NOT_FOUND, BlobImage, get_blob_store, parse_blob_ref
from tests.conftest import brasilia

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


@pytest.fixture
def make_detection(db: Session) -> Callable[..., Deteccao]:
    counter = iter(range(1, 10_000))

    def _make(
        greenhouse: Estufa | None,
        *,
        hours_ago: float = 1,
        cls: str = "fungico",
        confidence: str = "0.912345",
        alert: bool = True,
        read: bool | None = None,
        resolved: bool | None = None,
        heatmap: bool = True,
        bbox: bool = True,
    ) -> Deteccao:
        n = next(counter)
        when_utc = utcnow() - timedelta(hours=hours_ago)
        when = brasilia(when_utc)  # a Function grava DataHoraDeteccao em Brasília
        det = Deteccao(
            estufa_id=greenhouse.id if greenhouse else None,
            imagem_blob=f"capturas/estufa1/img-{n}.jpg",
            classe=cls,
            confianca=Decimal(confidence),
            prob_fungico=Decimal("0.9"),
            prob_bacteriano=Decimal("0.05"),
            prob_saudavel=Decimal("0.05"),
            prob_alface=Decimal("0.99"),
            patogeno_detectado=cls != "saudavel",
            alerta=alert and cls != "saudavel",
            modelo_versao="mobilenet-v3",
            modelo_dominio_versao="alface-v1",
            tempo_inferencia_ms=Decimal("123.456"),
            tempo_verificacao_ms=Decimal("10.5"),
            data_hora_deteccao=when,
            data_hora_gravacao=brasilia(when_utc + timedelta(seconds=5)),
            bbox_x=0.1 if bbox else None,
            bbox_y=0.2 if bbox else None,
            bbox_w=0.3 if bbox else None,
            bbox_h=0.4 if bbox else None,
            heatmap_blob=f"capturas/estufa1/heat-{n}.png" if heatmap else None,
            lido=read,
            resolvido=resolved,
        )
        db.add(det)
        db.commit()
        return det

    return _make


class FakeStore:
    def __init__(self) -> None:
        self.opened: list[str] = []

    def open_image(self, ref: str) -> BlobImage:
        self.opened.append(ref)
        if "missing" in ref:
            raise IMAGE_NOT_FOUND
        return BlobImage(iter([PNG[:10], PNG[10:]]), "image/png", len(PNG), '"etag-1"')


@pytest.fixture
def store(client) -> FakeStore:
    fake = FakeStore()
    client.app.dependency_overrides[get_blob_store] = lambda: fake
    return fake


@pytest.fixture
def scenario(make_greenhouse, make_user, login):
    g1, g2 = make_greenhouse("Estufa 1"), make_greenhouse("Estufa 2")
    make_user("user@x.com", greenhouses=(g1,))
    make_user("adm@x.com", admin=True)
    return g1, g2, login("user@x.com"), login("adm@x.com")


def test_list_newest_first_with_status_and_utc_times(client, scenario, make_detection):
    g1, _, user, _ = scenario
    old = make_detection(g1, hours_ago=5, read=True)
    new = make_detection(g1, hours_ago=1, cls="saudavel", resolved=True, heatmap=False, bbox=False)
    pending = make_detection(g1, hours_ago=3)
    response = client.get(f"/api/detections/{g1.id}", headers=user)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert [i["id"] for i in body["items"]] == [new.id, pending.id, old.id]
    first, second, third = body["items"]
    assert first["status"] == "resolved" and first["has_heatmap"] is False
    assert first["bbox"] is None and first["alert"] is False
    assert second["status"] == "pending" and third["status"] == "read"
    assert second["bbox"] == {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}
    assert second["confidence"] == pytest.approx(0.912345)
    assert second["probabilities"]["lettuce"] == pytest.approx(0.99)
    # Detecção em UTC; gravação (horário de Brasília no banco) convertida para UTC.
    assert second["detected_at"].endswith("Z") or second["detected_at"].endswith("+00:00")
    assert "imagem_blob" not in second and "image" not in second


def test_filters_by_class_status_alert_and_dates(client, scenario, make_detection):
    g1, _, user, _ = scenario
    make_detection(g1, hours_ago=1, cls="bacteriano")
    make_detection(g1, hours_ago=2, cls="saudavel")
    make_detection(g1, hours_ago=3, read=True, resolved=True)
    make_detection(g1, hours_ago=24 * 10)
    url = f"/api/detections/{g1.id}"

    def ids(**params):
        r = client.get(url, headers=user, params=params)
        assert r.status_code == 200, r.text
        return r.json()["total"]

    assert ids(**{"class": "bacteriano"}) == 1
    assert ids(status="resolved") == 1
    assert ids(status="pending") == 3
    assert ids(status="read") == 0
    assert ids(alert="true") == 3
    assert ids(alert="false") == 1
    today = utcnow().date()
    assert ids(start=str(today - timedelta(days=3)), end=str(today + timedelta(days=1))) == 3
    r = client.get(url, headers=user, params={"start": "2026-05-02", "end": "2026-05-01"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "invalid_range"
    assert client.get(url, headers=user, params={"class": "virus"}).status_code == 422


def test_pagination(client, scenario, make_detection):
    g1, _, user, _ = scenario
    for h in range(5):
        make_detection(g1, hours_ago=h + 1)
    r = client.get(f"/api/detections/{g1.id}", headers=user, params={"page": 2, "page_size": 2})
    body = r.json()
    assert body["total"] == 5 and body["page"] == 2 and len(body["items"]) == 2


def test_other_greenhouse_is_hidden(client, scenario, make_detection, store):
    g1, g2, user, adm = scenario
    other = make_detection(g2)
    make_detection(None)  # sem estufa: não aparece para ninguém
    assert client.get(f"/api/detections/{g2.id}", headers=user).status_code == 404
    assert client.get(f"/api/detections/{g2.id}/{other.id}", headers=user).status_code == 404
    r = client.get(f"/api/detections/{g2.id}/{other.id}/image", headers=user)
    assert r.status_code == 404 and store.opened == []
    # Detecção da estufa 2 pedida pela rota da estufa 1: também 404.
    r = client.get(f"/api/detections/{g1.id}/{other.id}", headers=user)
    assert r.json()["detail"]["code"] == "detection_not_found"
    assert client.get(f"/api/detections/{g2.id}", headers=adm).json()["total"] == 1


def test_requires_login(client, scenario, make_detection):
    g1, *_ = scenario
    det = make_detection(g1)
    assert client.get(f"/api/detections/{g1.id}").status_code == 401
    assert client.get(f"/api/detections/{g1.id}/{det.id}/image").status_code == 401


def test_detail(client, scenario, make_detection):
    g1, _, user, _ = scenario
    det = make_detection(g1)
    body = client.get(f"/api/detections/{g1.id}/{det.id}", headers=user).json()
    assert body["id"] == det.id and body["model_version"] == "mobilenet-v3"
    assert body["inference_ms"] == pytest.approx(123.456)


def test_image_and_heatmap_are_streamed(client, scenario, make_detection, store):
    g1, _, user, _ = scenario
    det = make_detection(g1)
    r = client.get(f"/api/detections/{g1.id}/{det.id}/image", headers=user)
    assert r.status_code == 200
    assert r.content == PNG
    assert r.headers["content-type"] == "image/png"
    assert r.headers["cache-control"] == "private, max-age=86400"
    assert r.headers["etag"] == '"etag-1"'
    r = client.get(
        f"/api/detections/{g1.id}/{det.id}/image", headers=user, params={"variant": "heatmap"}
    )
    assert r.status_code == 200
    assert store.opened == [det.imagem_blob, det.heatmap_blob]


def test_missing_heatmap_and_blob(client, scenario, make_detection, store, db):
    g1, _, user, _ = scenario
    det = make_detection(g1, heatmap=False)
    r = client.get(
        f"/api/detections/{g1.id}/{det.id}/image", headers=user, params={"variant": "heatmap"}
    )
    assert r.status_code == 404 and r.json()["detail"]["code"] == "image_not_found"
    det.imagem_blob = "capturas/missing.jpg"
    db.commit()
    r = client.get(f"/api/detections/{g1.id}/{det.id}/image", headers=user)
    assert r.status_code == 404


def test_storage_not_configured(client, scenario, make_detection):
    g1, _, user, _ = scenario
    det = make_detection(g1)
    r = client.get(f"/api/detections/{g1.id}/{det.id}/image", headers=user)
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "storage_not_configured"


def test_detection_time_is_brasilia_by_default(client, scenario, db, make_detection, monkeypatch):
    g1, _, user, _ = scenario
    det = make_detection(g1)
    # Como gravado pela Function: 22:08:57 em Brasília = 01:08:57 UTC do dia seguinte.
    det.data_hora_deteccao = datetime(2026, 11, 3, 22, 8, 57)
    db.commit()
    body = client.get(f"/api/detections/{g1.id}/{det.id}", headers=user).json()
    assert body["detected_at"].startswith("2026-11-04T01:08:57")
    # Filtro por dia local: a detecção pertence ao dia 03/11 em Brasília.
    url = f"/api/detections/{g1.id}"
    day = {"start": "2026-11-03", "end": "2026-11-03"}
    assert client.get(url, headers=user, params=day).json()["total"] == 1
    monkeypatch.setenv("DETECTION_TIME_IS_UTC", "true")
    get_settings.cache_clear()
    body = client.get(f"/api/detections/{g1.id}/{det.id}", headers=user).json()
    get_settings.cache_clear()
    assert body["detected_at"].startswith("2026-11-03T22:08:57")


# ---------- parse_blob_ref ----------


def _settings(**kw):
    base = {"blob_account_url": "https://conta.blob.core.windows.net"}
    base.update(kw)
    return get_settings().model_copy(update=base)


@pytest.mark.parametrize(
    ("raw", "kw", "expected"),
    [
        ("https://conta.blob.core.windows.net/imagens/a/b.jpg", {}, ("imagens", "a/b.jpg")),
        ("https://CONTA.blob.core.windows.net/imagens/a%20b.jpg", {}, ("imagens", "a b.jpg")),
        ("imagens/a/b.jpg", {}, ("imagens", "a/b.jpg")),
        ("a/b.jpg", {"blob_container": "imagens"}, ("imagens", "a/b.jpg")),
        ("imagens/a/b.jpg", {"blob_container": "imagens"}, ("imagens", "a/b.jpg")),
        (
            "http://127.0.0.1:10000/devstoreaccount1/imagens/x.png",
            {"blob_account_url": "http://127.0.0.1:10000/devstoreaccount1"},
            ("imagens", "x.png"),
        ),
    ],
)
def test_parse_blob_ref(raw, kw, expected):
    ref = parse_blob_ref(raw, _settings(**kw))
    assert (ref.container, ref.name) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "https://outra.blob.core.windows.net/imagens/a.jpg",  # outra conta: nunca busca
        "http://conta.blob.core.windows.net/imagens/a.jpg",  # esquema diferente
        "https://conta.blob.core.windows.net/imagens",
        "so-o-nome.jpg",
        "imagens/../segredo.jpg",
        "",
    ],
)
def test_parse_blob_ref_rejects(raw):
    with pytest.raises(type(IMAGE_NOT_FOUND)):
        parse_blob_ref(raw, _settings())


def test_image_type_helper():
    assert blob_store._image_type("image/jpeg", "a.bin") == "image/jpeg"
    assert blob_store._image_type("application/octet-stream", "a.png") == "image/png"
    assert blob_store._image_type("text/html", "a.html") is None


# ---------- AzureBlobStore (cliente do SDK simulado) ----------


class _Props:
    def __init__(self, ctype="image/jpeg", size=100):
        from types import SimpleNamespace

        self.content_settings = SimpleNamespace(content_type=ctype)
        self.size = size
        self.etag = '"e"'


class _Downloader:
    def chunks(self):
        return iter([b"abc"])


class _BlobClient:
    def __init__(self, props=None, error=None):
        self.props, self.error = props or _Props(), error

    def get_blob_properties(self):
        if self.error:
            raise self.error
        return self.props

    def download_blob(self, **_):
        return _Downloader()


class _ServiceClient:
    def __init__(self, blob):
        self.blob, self.calls = blob, []

    def get_blob_client(self, container, name):
        self.calls.append((container, name))
        return self.blob


def _store(blob, **kw):
    store = blob_store.AzureBlobStore.__new__(blob_store.AzureBlobStore)
    store.settings = _settings(blob_container="imagens", **kw)
    store.client = _ServiceClient(blob)
    return store


def test_azure_store_reads_image():
    store = _store(_BlobClient())
    image = store.open_image("estufa-01/2026/11/a.jpg")
    assert list(image.chunks) == [b"abc"] and image.content_type == "image/jpeg"
    assert store.client.calls == [("imagens", "estufa-01/2026/11/a.jpg")]


@pytest.mark.parametrize(
    ("blob", "code"),
    [
        (_BlobClient(_Props(ctype="text/html")), "image_not_found"),
        (_BlobClient(_Props(size=50 * 1024 * 1024)), "image_not_found"),
    ],
)
def test_azure_store_rejects(blob, code):
    with pytest.raises(type(IMAGE_NOT_FOUND)) as exc:
        _store(blob).open_image("a/b.jpg")
    assert exc.value.code == code


def test_azure_store_errors():
    from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError

    with pytest.raises(type(IMAGE_NOT_FOUND)) as exc:
        _store(_BlobClient(error=ResourceNotFoundError("x"))).open_image("a/b.jpg")
    assert exc.value.code == "image_not_found"
    with pytest.raises(type(IMAGE_NOT_FOUND)) as exc:
        _store(_BlobClient(error=ServiceRequestError("x"))).open_image("a/b.jpg")
    assert exc.value.code == "storage_unavailable"


def test_azure_store_construction(monkeypatch):
    monkeypatch.setenv("BLOB_CONNECTION_STRING", "UseDevelopmentStorage=true")
    get_settings.cache_clear()
    blob_store._azure_store.cache_clear()
    try:
        store = blob_store.get_blob_store()
        assert isinstance(store, blob_store.AzureBlobStore)
    finally:
        monkeypatch.delenv("BLOB_CONNECTION_STRING")
        get_settings.cache_clear()
        blob_store._azure_store.cache_clear()
    store = blob_store.AzureBlobStore(_settings())
    assert store.client.url.startswith("https://conta.blob.core.windows.net")
    assert type(store.client.credential).__name__ == "DefaultAzureCredential"


def test_azure_store_sas_and_anonymous():
    from azure.core.credentials import AzureSasCredential
    from pydantic import SecretStr

    store = blob_store.AzureBlobStore(_settings(blob_sas_token=SecretStr("sv=2024&sig=abc")))
    assert isinstance(store.client.credential, AzureSasCredential)
    store = blob_store.AzureBlobStore(_settings(blob_anonymous=True))
    assert store.client.credential is None


def test_blob_settings_validation(monkeypatch):
    from app.core.config import Settings

    assert Settings(blob_account_url=" https://c.blob.core.windows.net/ ").blob_account_url == (
        "https://c.blob.core.windows.net"
    )
    assert Settings(blob_container="  ").blob_container is None
    assert Settings(blob_sas_token=" ").blob_sas_token is None
    assert Settings(blob_sas_token="?sv=1&sig=x").blob_sas_token.get_secret_value() == "sv=1&sig=x"
    with pytest.raises(ValueError, match="BLOB_ACCOUNT_URL"):
        Settings(
            app_env="production",
            jwt_secret="x" * 40,
            database_url="mssql+pyodbc://u:p@h/db",
            blob_account_url="http://c.blob.core.windows.net",
        )
