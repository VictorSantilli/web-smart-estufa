from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.greenhouse import GreenhouseOut

Level = Literal["low", "ok", "warning", "critical"]


class Measurement(BaseModel):
    value: float | None = Field(description="Valor da última leitura com dado válido")
    level: Level | None = Field(description="Faixa: low, ok, warning ou critical")
    measured_at: datetime | None = Field(description="Hora da medição desse valor (UTC)")
    is_current: bool = Field(
        description="False quando a leitura mais recente veio nula e o valor é de uma anterior"
    )


class SensorStatus(BaseModel):
    ok: bool = Field(description="False quando a leitura mais recente veio sem valor (falha)")
    temperature: Measurement
    humidity: Measurement


class FansStatus(BaseModel):
    state: Literal["on", "off", "unknown"]
    measured_at: datetime | None


class Thresholds(BaseModel):
    temp_min: float
    temp_warning: float
    temp_critical: float
    humidity_min: float
    humidity_max: float


class DashboardResponse(BaseModel):
    greenhouse: GreenhouseOut
    has_data: bool
    last_reading_at: datetime | None = Field(description="Hora da última medição (UTC)")
    last_communication_at: datetime | None = Field(
        description="Hora em que o último dado chegou ao banco (UTC)"
    )
    is_online: bool
    stale_after_minutes: int
    canopy: SensorStatus = Field(description="Sensor do dossel (altura das plantas)")
    ceiling: SensorStatus = Field(description="Sensor do teto")
    fans: FansStatus
    thresholds: Thresholds
    generated_at: datetime


class LatestReadingResponse(BaseModel):
    id: int
    device_id: str
    measured_at: datetime
    recorded_at: datetime | None
    canopy_temperature: float | None
    canopy_humidity: float | None
    ceiling_temperature: float | None
    ceiling_humidity: float | None
    fans_on: bool | None


class DeviceOut(BaseModel):
    device_id: str
    description: str | None
    is_active: bool
    last_reading_at: datetime | None
    last_communication_at: datetime | None
    is_online: bool
