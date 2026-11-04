from datetime import datetime

from sqlalchemy import Select, false, func, or_, select, true
from sqlalchemy.orm import Session

from app.models import Deteccao


def _is_true(column):
    return column == true()


def _not_true(column):
    return or_(column.is_(None), column == false())


class DetectionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _filtered(
        self,
        greenhouse_id: int,
        *,
        start: datetime | None,
        end: datetime | None,
        detection_class: str | None,
        status: str | None,
        alert: bool | None,
    ) -> Select:
        stmt = select(Deteccao).where(Deteccao.estufa_id == greenhouse_id)
        if start is not None:
            stmt = stmt.where(Deteccao.data_hora_deteccao >= start)
        if end is not None:
            stmt = stmt.where(Deteccao.data_hora_deteccao < end)
        if detection_class is not None:
            stmt = stmt.where(Deteccao.classe == detection_class)
        if alert is not None:
            stmt = stmt.where(Deteccao.alerta == (true() if alert else false()))
        if status == "resolved":
            stmt = stmt.where(_is_true(Deteccao.resolvido))
        elif status == "read":
            stmt = stmt.where(_is_true(Deteccao.lido), _not_true(Deteccao.resolvido))
        elif status == "pending":
            stmt = stmt.where(_not_true(Deteccao.lido), _not_true(Deteccao.resolvido))
        return stmt

    def list(
        self,
        greenhouse_id: int,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        detection_class: str | None = None,
        status: str | None = None,
        alert: bool | None = None,
        offset: int = 0,
        limit: int = 24,
    ) -> tuple[list[Deteccao], int]:
        stmt = self._filtered(
            greenhouse_id,
            start=start,
            end=end,
            detection_class=detection_class,
            status=status,
            alert=alert,
        )
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.scalars(
            stmt.order_by(Deteccao.data_hora_deteccao.desc(), Deteccao.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return list(rows), total

    def get(self, greenhouse_id: int, detection_id: int) -> Deteccao | None:
        stmt = select(Deteccao).where(
            Deteccao.id == detection_id, Deteccao.estufa_id == greenhouse_id
        )
        return self.db.scalar(stmt)
