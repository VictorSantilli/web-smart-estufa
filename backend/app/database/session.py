from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    url = settings.database_url.get_secret_value()
    if url.startswith("sqlite"):
        # Usado apenas em testes unitários.
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.database_echo,
        )
    return create_engine(
        url,
        pool_size=settings.database_pool_size,
        pool_pre_ping=True,  # o Azure SQL fecha conexões ociosas
        pool_recycle=1800,
        echo=settings.database_echo,
    )


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    session = _session_factory()()
    try:
        yield session
    finally:
        session.close()


def ping_database() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
