from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    """Agora em UTC, sem tzinfo (as colunas DATETIME2 do banco não guardam fuso)."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc(value: datetime | None) -> datetime | None:
    """Marca um datetime ingênuo que JÁ está em UTC (ex.: DataHoraEnvio) como UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def local_to_utc(value: datetime | None, tz_name: str) -> datetime | None:
    """Converte um datetime ingênuo em horário local (ex.: DataHoraGravacao) para UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=ZoneInfo(tz_name)).astimezone(UTC)
