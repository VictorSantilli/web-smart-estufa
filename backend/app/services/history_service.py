"""Histórico de leituras: últimas 24 h (cada medição) e agregados diários.

Regras:
- O intervalo é sempre filtrado por DataHoraEnvio (hora da medição, UTC).
- 24h: janela móvel das últimas 24 horas, com cada medição.
- 7d / 30d: os últimos 7 ou 30 dias do calendário local, incluindo hoje, por dia.
- Personalizado: datas locais (início e fim inclusivos), no máximo HISTORY_MAX_DAYS dias.
  Até 2 dias mostra cada medição; acima disso, agregados por dia.
- Medições repetidas (mesmo DeviceId e DataHoraEnvio) contam uma vez.
- Dias sem dados aparecem com samples = 0 e valores nulos, para o gráfico mostrar a falha.
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.clock import as_utc
from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Estufa
from app.repositories.reading_repository import HistoryRepository
from app.schemas.dashboard import Thresholds
from app.schemas.history import DailyPoint, DailyStats, HistoryResponse, RawPoint

RAW_MAX_DAYS = 2
SERIES = {
    # campo da resposta: coluna da consulta
    "canopy_temperature": "temperature",
    "canopy_humidity": "humidity",
    "ceiling_temperature": "ceiling_temperature",
    "ceiling_humidity": "ceiling_humidity",
}


def _round(value: Decimal | float | None) -> float | None:
    return None if value is None else round(float(value), 2)


def _as_date(value: date | str) -> date:
    # SQL Server devolve date; o SQLite dos testes devolve texto "AAAA-MM-DD".
    return value if isinstance(value, date) else date.fromisoformat(value)


class HistoryService:
    def __init__(self, db: Session, now: datetime | None = None) -> None:
        self.repo = HistoryRepository(db)
        self.settings = get_settings()
        self.tz = ZoneInfo(self.settings.app_timezone)
        self.now = now or datetime.now(UTC)

    # ---------- intervalo ----------

    def _local_midnight_utc(self, day: date) -> datetime:
        return datetime.combine(day, time.min, tzinfo=self.tz).astimezone(UTC)

    def _today(self) -> date:
        return self.now.astimezone(self.tz).date()

    def resolve_range(
        self, period: str | None, start: date | None, end: date | None
    ) -> tuple[str, str, datetime, datetime, date | None, date | None]:
        """Devolve (period, granularity, início UTC, fim UTC, primeiro dia, último dia)."""
        if start is not None or end is not None:
            if period is not None:
                raise AppError(
                    422, "invalid_range", "Informe um período ou datas de início e fim, não ambos."
                )
            if start is None or end is None:
                raise AppError(422, "invalid_range", "Informe a data de início e a data de fim.")
            if start > end:
                raise AppError(
                    422, "invalid_range", "A data de início deve ser anterior à data de fim."
                )
            if end > self._today():
                raise AppError(422, "invalid_range", "A data de fim não pode estar no futuro.")
            days = (end - start).days + 1
            limit = self.settings.history_max_days
            if days > limit:
                raise AppError(
                    422,
                    "range_too_long",
                    f"O período personalizado pode ter no máximo {limit} dias.",
                )
            granularity = "raw" if days <= RAW_MAX_DAYS else "daily"
            return (
                "custom",
                granularity,
                self._local_midnight_utc(start),
                self._local_midnight_utc(end + timedelta(days=1)),
                start,
                end,
            )

        period = period or "24h"
        if period == "24h":
            return period, "raw", self.now - timedelta(hours=24), self.now, None, None
        days = 7 if period == "7d" else 30
        today = self._today()
        first = today - timedelta(days=days - 1)
        return (
            period,
            "daily",
            self._local_midnight_utc(first),
            self._local_midnight_utc(today + timedelta(days=1)),
            first,
            today,
        )

    # ---------- caso de uso ----------

    def history(
        self, greenhouse: Estufa, period: str | None, start: date | None, end: date | None
    ) -> HistoryResponse:
        period, granularity, start_utc, end_utc, first, last = self.resolve_range(
            period, start, end
        )
        # As colunas DATETIME2 não guardam fuso: a consulta usa UTC sem tzinfo.
        q_start = start_utc.replace(tzinfo=None)
        q_end = end_utc.replace(tzinfo=None)

        points: list[RawPoint] = []
        days: list[DailyPoint] = []
        if granularity == "raw":
            points = [
                RawPoint(
                    measured_at=as_utc(row["sent_at"]),
                    device_id=row["device_id"],
                    **{field: _round(row[col]) for field, col in SERIES.items()},
                )
                for row in self.repo.raw(greenhouse.id, q_start, q_end)
            ]
        else:
            rows = self.repo.daily(
                greenhouse.id,
                q_start,
                q_end,
                self.settings.db_local_timezone,
                self.settings.app_timezone,
            )
            by_day = {_as_date(row["day"]): row for row in rows}
            empty = DailyStats(min=None, avg=None, max=None)
            day = first
            while day <= last:
                row = by_day.get(day)
                stats = {
                    field: DailyStats(
                        min=_round(row[f"{col}_min"]),
                        avg=_round(row[f"{col}_avg"]),
                        max=_round(row[f"{col}_max"]),
                    )
                    if row
                    else empty
                    for field, col in SERIES.items()
                }
                days.append(DailyPoint(date=day, samples=row["samples"] if row else 0, **stats))
                day += timedelta(days=1)

        s = self.settings
        return HistoryResponse(
            greenhouse_id=greenhouse.id,
            period=period,
            granularity=granularity,
            start=start_utc,
            end=end_utc,
            timezone=s.app_timezone,
            points=points,
            days=days,
            thresholds=Thresholds(
                temp_min=s.temp_min,
                temp_warning=s.temp_warning,
                temp_critical=s.temp_critical,
                humidity_min=s.humidity_min,
                humidity_max=s.humidity_max,
            ),
        )
