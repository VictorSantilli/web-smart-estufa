"""Classificação dos valores nas faixas definidas para o projeto (variáveis de ambiente)."""

from decimal import Decimal
from typing import Literal

from app.core.config import Settings

Level = Literal["low", "ok", "warning", "critical"]


def classify_temperature(value: Decimal | float | None, s: Settings) -> Level | None:
    """< mín: low (azul) · até 25: ok (verde) · >25 até 26: warning (laranja) · >26: critical."""
    if value is None:
        return None
    v = float(value)
    if v < s.temp_min:
        return "low"
    if v > s.temp_critical:
        return "critical"
    if v > s.temp_warning:
        return "warning"
    return "ok"


def classify_humidity(value: Decimal | float | None, s: Settings) -> Level | None:
    """< mín: low · mín..máx: ok · > máx (risco de fungos): warning."""
    if value is None:
        return None
    v = float(value)
    if v < s.humidity_min:
        return "low"
    if v > s.humidity_max:
        return "warning"
    return "ok"
