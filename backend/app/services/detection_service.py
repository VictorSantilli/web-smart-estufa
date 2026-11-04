"""Histórico das detecções da IA (tabela Deteccoes, gravada pela Function de visão).

- Só entram detecções com EstufaId da estufa autorizada; a checagem de acesso é feita
  antes, em `require_greenhouse_access`.
- Filtro de datas em dias do calendário local (inclusivos), convertidos para o fuso em que
  DataHoraDeteccao é gravada (DETECTION_TIME_IS_UTC).
- Status: resolvida (Resolvido = 1) > lida (Lido = 1) > pendente.
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.clock import as_utc, local_to_utc
from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Deteccao, Estufa
from app.repositories.detection_repository import DetectionRepository
from app.schemas.common import Page
from app.schemas.detection import BoundingBox, DetectionItem, Probabilities

DETECTION_NOT_FOUND = AppError(404, "detection_not_found", "Detecção não encontrada.")


def _float(value: Decimal | float | None) -> float | None:
    return None if value is None else float(value)


def status_of(det: Deteccao) -> str:
    if det.resolvido:
        return "resolved"
    if det.lido:
        return "read"
    return "pending"


class DetectionService:
    def __init__(self, db: Session) -> None:
        self.repo = DetectionRepository(db)
        self.settings = get_settings()
        self.tz = ZoneInfo(self.settings.app_timezone)

    # ---------- horários ----------

    def _detected_utc(self, value: datetime) -> datetime:
        if self.settings.detection_time_is_utc:
            return as_utc(value)
        return local_to_utc(value, self.settings.db_local_timezone_iana)

    def _db_bound(self, day: date) -> datetime:
        """Meia-noite local do dia, no fuso em que DataHoraDeteccao é gravada (sem tzinfo)."""
        local = datetime.combine(day, time.min, tzinfo=self.tz)
        if self.settings.detection_time_is_utc:
            return local.astimezone(UTC).replace(tzinfo=None)
        return local.astimezone(ZoneInfo(self.settings.db_local_timezone_iana)).replace(tzinfo=None)

    # ---------- consultas ----------

    def to_item(self, det: Deteccao) -> DetectionItem:
        bbox = None
        if None not in (det.bbox_x, det.bbox_y, det.bbox_w, det.bbox_h):
            bbox = BoundingBox(x=det.bbox_x, y=det.bbox_y, w=det.bbox_w, h=det.bbox_h)
        return DetectionItem(
            id=det.id,
            greenhouse_id=det.estufa_id,
            detected_at=self._detected_utc(det.data_hora_deteccao),
            recorded_at=local_to_utc(det.data_hora_gravacao, self.settings.db_local_timezone_iana),
            detection_class=det.classe,
            confidence=float(det.confianca),
            probabilities=Probabilities(
                fungal=_float(det.prob_fungico),
                bacterial=_float(det.prob_bacteriano),
                healthy=_float(det.prob_saudavel),
                lettuce=_float(det.prob_alface),
            ),
            pathogen_detected=det.patogeno_detectado,
            alert=det.alerta,
            status=status_of(det),
            has_heatmap=bool(det.heatmap_blob),
            bbox=bbox,
            model_version=det.modelo_versao,
            domain_model_version=det.modelo_dominio_versao,
            inference_ms=float(det.tempo_inferencia_ms),
            verification_ms=_float(det.tempo_verificacao_ms),
        )

    def list(
        self,
        greenhouse: Estufa,
        *,
        start: date | None,
        end: date | None,
        detection_class: str | None,
        status: str | None,
        alert: bool | None,
        page: int,
        page_size: int,
    ) -> Page[DetectionItem]:
        if start is not None and end is not None and start > end:
            raise AppError(
                422, "invalid_range", "A data de início deve ser anterior à data de fim."
            )
        page_size = min(page_size, self.settings.detections_page_size_max)
        rows, total = self.repo.list(
            greenhouse.id,
            start=self._db_bound(start) if start else None,
            end=self._db_bound(end + timedelta(days=1)) if end else None,
            detection_class=detection_class,
            status=status,
            alert=alert,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return Page[DetectionItem](
            items=[self.to_item(r) for r in rows], total=total, page=page, page_size=page_size
        )

    def get(self, greenhouse: Estufa, detection_id: int) -> Deteccao:
        det = self.repo.get(greenhouse.id, detection_id)
        if det is None:
            raise DETECTION_NOT_FOUND
        return det
