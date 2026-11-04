from datetime import UTC, datetime


def utcnow() -> datetime:
    """Agora em UTC, sem tzinfo (as colunas DATETIME2 do banco não guardam fuso)."""
    return datetime.now(UTC).replace(tzinfo=None)
