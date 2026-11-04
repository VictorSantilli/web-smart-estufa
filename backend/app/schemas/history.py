import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.dashboard import Thresholds

Period = Literal["24h", "7d", "30d", "custom"]
Granularity = Literal["raw", "daily"]


class RawPoint(BaseModel):
    measured_at: dt.datetime = Field(description="Hora da medição (UTC)")
    device_id: str
    canopy_temperature: float | None
    canopy_humidity: float | None
    ceiling_temperature: float | None
    ceiling_humidity: float | None


class DailyStats(BaseModel):
    min: float | None
    avg: float | None
    max: float | None


class DailyPoint(BaseModel):
    date: dt.date = Field(description="Dia no fuso do projeto")
    samples: int = Field(description="Quantidade de medições no dia (0 = dia sem dados)")
    canopy_temperature: DailyStats
    canopy_humidity: DailyStats
    ceiling_temperature: DailyStats
    ceiling_humidity: DailyStats


class HistoryResponse(BaseModel):
    greenhouse_id: int
    period: Period
    granularity: Granularity = Field(
        description="raw: cada medição; daily: mínimo, média e máximo por dia"
    )
    start: dt.datetime = Field(description="Início do intervalo (UTC, inclusivo)")
    end: dt.datetime = Field(description="Fim do intervalo (UTC, exclusivo)")
    timezone: str = Field(description="Fuso usado para os dias e para exibição")
    points: list[RawPoint] = Field(description="Preenchido quando granularity = raw")
    days: list[DailyPoint] = Field(
        description="Preenchido quando granularity = daily; inclui dias sem dados (samples = 0)"
    )
    thresholds: Thresholds
