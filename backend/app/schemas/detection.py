import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

DetectionClass = Literal["fungico", "bacteriano", "saudavel"]
DetectionStatus = Literal["pending", "read", "resolved"]


class Probabilities(BaseModel):
    fungal: float | None
    bacterial: float | None
    healthy: float | None
    lettuce: float | None = Field(description="Probabilidade de a imagem ser de alface")


class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class DetectionItem(BaseModel):
    id: int
    greenhouse_id: int
    detected_at: dt.datetime = Field(description="Hora da captura/detecção (UTC)")
    recorded_at: dt.datetime | None = Field(description="Hora em que foi gravada no banco (UTC)")
    detection_class: DetectionClass
    confidence: float
    probabilities: Probabilities
    pathogen_detected: bool
    alert: bool
    status: DetectionStatus = Field(
        description="pending (não lida), read (lida) ou resolved (resolvida)"
    )
    has_heatmap: bool
    bbox: BoundingBox | None
    model_version: str
    domain_model_version: str | None
    inference_ms: float
    verification_ms: float | None
