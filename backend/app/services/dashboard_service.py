"""Indicadores do Dashboard: última leitura, situação dos sensores e comunicação."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.clock import as_utc, local_to_utc
from app.core.config import get_settings
from app.models import Estufa, LeituraSensor
from app.repositories.reading_repository import ReadingRepository
from app.schemas.dashboard import (
    DashboardResponse,
    DeviceOut,
    FansStatus,
    LatestReadingResponse,
    Measurement,
    SensorStatus,
    Thresholds,
)
from app.schemas.greenhouse import GreenhouseOut
from app.services.thresholds import classify_humidity, classify_temperature

L = LeituraSensor


def _float(value) -> float | None:
    return None if value is None else float(value)


class DashboardService:
    def __init__(self, db: Session, now: datetime | None = None) -> None:
        self.readings = ReadingRepository(db)
        self.settings = get_settings()
        self.now = now or datetime.now(UTC)

    # ---------- helpers ----------

    def _recorded_to_utc(self, value: datetime | None) -> datetime | None:
        return local_to_utc(value, self.settings.db_local_timezone_iana)

    def _is_online(self, last_communication: datetime | None) -> bool:
        if last_communication is None:
            return False
        return self.now - last_communication <= timedelta(minutes=self.settings.stale_after_minutes)

    def _measurement(self, greenhouse_id, latest: LeituraSensor | None, column, classify):
        attr = column.key  # nome do atributo no modelo (ex.: "temperatura")
        current = getattr(latest, attr) if latest else None
        if current is not None:
            return Measurement(
                value=float(current),
                level=classify(current, self.settings),
                measured_at=as_utc(latest.data_hora_envio),
                is_current=True,
            )
        # Leitura mais recente veio nula (sensor falhou): mostra o último valor válido.
        previous = self.readings.latest_with_value(greenhouse_id, column) if latest else None
        value = getattr(previous, attr) if previous else None
        return Measurement(
            value=_float(value),
            level=classify(value, self.settings),
            measured_at=as_utc(previous.data_hora_envio) if previous else None,
            is_current=False,
        )

    def _sensor(self, greenhouse_id, latest, temp_col, hum_col) -> SensorStatus:
        ok = (
            latest is not None
            and getattr(latest, temp_col.key) is not None
            and getattr(latest, hum_col.key) is not None
        )
        return SensorStatus(
            ok=ok,
            temperature=self._measurement(greenhouse_id, latest, temp_col, classify_temperature),
            humidity=self._measurement(greenhouse_id, latest, hum_col, classify_humidity),
        )

    # ---------- casos de uso ----------

    def dashboard(self, greenhouse: Estufa) -> DashboardResponse:
        gid = greenhouse.id
        latest = self.readings.latest(gid)
        last_reading_at = as_utc(latest.data_hora_envio) if latest else None
        last_communication_at = (
            self._recorded_to_utc(self.readings.last_recorded_at(gid)) or last_reading_at
        )
        s = self.settings

        if latest is None or latest.ventoinhas is None:
            fans = FansStatus(state="unknown", measured_at=None)
        else:
            fans = FansStatus(
                state="on" if latest.ventoinhas else "off", measured_at=last_reading_at
            )

        return DashboardResponse(
            greenhouse=GreenhouseOut(id=gid, name=greenhouse.nome),
            has_data=latest is not None,
            last_reading_at=last_reading_at,
            last_communication_at=last_communication_at,
            is_online=self._is_online(last_communication_at),
            stale_after_minutes=s.stale_after_minutes,
            canopy=self._sensor(gid, latest, L.temperatura, L.umidade),
            ceiling=self._sensor(gid, latest, L.temp_teto, L.umid_teto),
            fans=fans,
            thresholds=Thresholds(
                temp_min=s.temp_min,
                temp_warning=s.temp_warning,
                temp_critical=s.temp_critical,
                humidity_min=s.humidity_min,
                humidity_max=s.humidity_max,
            ),
            generated_at=self.now,
        )

    def latest_reading(self, greenhouse: Estufa) -> LatestReadingResponse | None:
        r = self.readings.latest(greenhouse.id)
        if r is None:
            return None
        return LatestReadingResponse(
            id=r.id,
            device_id=r.device_id,
            measured_at=as_utc(r.data_hora_envio),
            recorded_at=self._recorded_to_utc(r.data_hora_gravacao),
            canopy_temperature=_float(r.temperatura),
            canopy_humidity=_float(r.umidade),
            ceiling_temperature=_float(r.temp_teto),
            ceiling_humidity=_float(r.umid_teto),
            fans_on=r.ventoinhas,
        )

    def devices(self, greenhouse: Estufa) -> list[DeviceOut]:
        result = []
        for device, last_sent, last_recorded in self.readings.devices_with_last_contact(
            greenhouse.id
        ):
            last_reading_at = as_utc(last_sent)
            last_comm = self._recorded_to_utc(last_recorded) or last_reading_at
            result.append(
                DeviceOut(
                    device_id=device.device_id,
                    description=device.descricao,
                    is_active=device.ativo,
                    last_reading_at=last_reading_at,
                    last_communication_at=last_comm,
                    is_online=self._is_online(last_comm),
                )
            )
        return result
