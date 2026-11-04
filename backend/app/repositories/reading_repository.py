"""Consultas de leituras de sensores de UMA estufa.

Uma leitura pertence à estufa quando:
  - LeiturasSensores.IdEstufa é a estufa; ou
  - IdEstufa é nulo e o DeviceId está cadastrado em Dispositivos para a estufa.
Isso cobre as leituras gravadas sem IdEstufa pela Function (regra aprovada na Etapa 1).
"""

from datetime import datetime

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import Dispositivo, LeituraSensor

L = LeituraSensor


def belongs_to_greenhouse(greenhouse_id: int) -> ColumnElement[bool]:
    devices = select(Dispositivo.device_id).where(Dispositivo.estufa_id == greenhouse_id)
    return or_(
        L.id_estufa == greenhouse_id,
        and_(L.id_estufa.is_(None), L.device_id.in_(devices)),
    )


class ReadingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def latest(self, greenhouse_id: int) -> LeituraSensor | None:
        stmt = (
            select(L)
            .where(belongs_to_greenhouse(greenhouse_id))
            .order_by(L.data_hora_envio.desc(), L.id.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def latest_with_value(self, greenhouse_id: int, column) -> LeituraSensor | None:
        """Última leitura em que a coluna informada não é nula (último valor válido)."""
        stmt = (
            select(L)
            .where(belongs_to_greenhouse(greenhouse_id), column.is_not(None))
            .order_by(L.data_hora_envio.desc(), L.id.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def last_recorded_at(self, greenhouse_id: int) -> datetime | None:
        """MAX(DataHoraGravacao), no horário de Brasília (como está no banco)."""
        stmt = select(func.max(L.data_hora_gravacao)).where(belongs_to_greenhouse(greenhouse_id))
        return self.db.scalar(stmt)

    def devices_with_last_contact(
        self, greenhouse_id: int
    ) -> list[tuple[Dispositivo, datetime | None, datetime | None]]:
        """Dispositivos da estufa com MAX(DataHoraEnvio) e MAX(DataHoraGravacao) de cada um."""
        last = (
            select(
                L.device_id.label("device_id"),
                func.max(L.data_hora_envio).label("last_sent"),
                func.max(L.data_hora_gravacao).label("last_recorded"),
            )
            .group_by(L.device_id)
            .subquery()
        )
        stmt = (
            select(Dispositivo, last.c.last_sent, last.c.last_recorded)
            .outerjoin(last, last.c.device_id == Dispositivo.device_id)
            .where(Dispositivo.estufa_id == greenhouse_id)
            .order_by(Dispositivo.device_id)
        )
        return [(d, sent, recorded) for d, sent, recorded in self.db.execute(stmt).all()]
