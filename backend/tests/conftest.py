import os

# Configuração isolada para testes: banco SQLite em memória, sem .env do desenvolvedor.
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["FRONTEND_DIST_DIR"] = "/nonexistent"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 32

from collections.abc import Callable, Iterator  # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.clock import utcnow  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.rate_limit import login_ip_limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import _session_factory, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Dispositivo, Estufa, LeituraSensor, Usuario, UsuarioEstufa  # noqa: E402

PASSWORD = "Senha123"
_HASH_CACHE: dict[str, str] = {}


def cached_hash(password: str) -> str:
    """bcrypt é lento de propósito; nos testes cada senha é calculada uma vez só."""
    if password not in _HASH_CACHE:
        _HASH_CACHE[password] = hash_password(password)
    return _HASH_CACHE[password]


@pytest.fixture(autouse=True)
def _database() -> Iterator[None]:
    """Cria as tabelas no SQLite (somente nos testes; no Azure elas já existem)."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    login_ip_limiter.reset()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db() -> Iterator[Session]:
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(create_app())


@pytest.fixture
def make_greenhouse(db: Session) -> Callable[..., Estufa]:
    def _make(name: str) -> Estufa:
        greenhouse = Estufa(nome=name, data_criacao=utcnow())
        db.add(greenhouse)
        db.commit()
        return greenhouse

    return _make


@pytest.fixture
def make_user(db: Session) -> Callable[..., Usuario]:
    def _make(
        email: str,
        *,
        admin: bool = False,
        active: bool = True,
        greenhouses: tuple[Estufa, ...] = (),
        password: str = PASSWORD,
    ) -> Usuario:
        user = Usuario(
            email=email,
            nome=email.split("@")[0].title(),
            senha_hash=cached_hash(password),
            data_criacao=utcnow(),
            adm=admin,
            ativo=active,
            tentativas_falhas=0,
            token_versao=0,
        )
        db.add(user)
        db.flush()
        for g in greenhouses:
            db.add(UsuarioEstufa(usuario_id=user.id, estufa_id=g.id, data_vinculo=date.today()))
        db.commit()
        return user

    return _make


@pytest.fixture
def login(client: TestClient) -> Callable[[str], dict[str, str]]:
    """Faz login e devolve o cabeçalho Authorization."""

    def _login(email: str, password: str = PASSWORD) -> dict[str, str]:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture
def make_device(db: Session) -> Callable[..., Dispositivo]:
    def _make(device_id: str, greenhouse: Estufa) -> Dispositivo:
        device = Dispositivo(
            device_id=device_id, estufa_id=greenhouse.id, ativo=True, data_criacao=utcnow()
        )
        db.add(device)
        db.commit()
        return device

    return _make


def brasilia(utc_naive: datetime) -> datetime:
    """Simula o DEFAULT do banco: DataHoraGravacao no horário de Brasília."""
    return (
        utc_naive.replace(tzinfo=ZoneInfo("UTC"))
        .astimezone(ZoneInfo("America/Sao_Paulo"))
        .replace(tzinfo=None)
    )


@pytest.fixture
def make_reading(db: Session) -> Callable[..., LeituraSensor]:
    """Cria uma leitura medida há `minutes_ago` minutos (gravada `delay_s` segundos depois)."""

    def _make(
        greenhouse: Estufa | None,
        *,
        minutes_ago: float = 1,
        device_id: str = "esp32-01",
        temp: float | None = 22,
        hum: float | None = 75,
        temp_ceiling: float | None = 24,
        hum_ceiling: float | None = 70,
        fans: bool | None = None,
        delay_s: float = 2,
        recorded: bool = True,
    ) -> LeituraSensor:
        sent = utcnow() - timedelta(minutes=minutes_ago)
        reading = LeituraSensor(
            device_id=device_id,
            temperatura=temp,
            umidade=hum,
            temp_teto=temp_ceiling,
            umid_teto=hum_ceiling,
            data_hora_envio=sent,
            data_hora_gravacao=brasilia(sent + timedelta(seconds=delay_s)) if recorded else None,
            id_estufa=greenhouse.id if greenhouse else None,
            ventoinhas=fans,
        )
        db.add(reading)
        db.commit()
        return reading

    return _make
