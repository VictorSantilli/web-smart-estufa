from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse

from app.api.deps import AuthorizedGreenhouse, DbSession
from app.schemas.common import Page
from app.schemas.detection import DetectionClass, DetectionItem, DetectionStatus
from app.services.detection_service import DetectionService
from app.storage.blob_store import IMAGE_NOT_FOUND, BlobStore, get_blob_store

router = APIRouter(prefix="/detections", tags=["detections"])

DetectionId = Annotated[int, Path(ge=1)]


@router.get(
    "/{greenhouse_id}",
    response_model=Page[DetectionItem],
    summary="Histórico das detecções da IA na estufa (mais recentes primeiro)",
    responses={404: {"description": "Estufa sem acesso"}, 422: {"description": "Filtro inválido"}},
)
def list_detections(
    greenhouse: AuthorizedGreenhouse,
    db: DbSession,
    start: Annotated[date | None, Query(description="Data inicial local (AAAA-MM-DD)")] = None,
    end: Annotated[date | None, Query(description="Data final local, inclusiva")] = None,
    detection_class: Annotated[DetectionClass | None, Query(alias="class")] = None,
    status: Annotated[DetectionStatus | None, Query()] = None,
    alert: Annotated[bool | None, Query(description="Com (true) ou sem (false) alerta")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
):
    return DetectionService(db).list(
        greenhouse,
        start=start,
        end=end,
        detection_class=detection_class,
        status=status,
        alert=alert,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{greenhouse_id}/{detection_id}",
    response_model=DetectionItem,
    summary="Detalhe de uma detecção",
    responses={404: {"description": "Estufa ou detecção sem acesso"}},
)
def get_detection(greenhouse: AuthorizedGreenhouse, db: DbSession, detection_id: DetectionId):
    service = DetectionService(db)
    return service.to_item(service.get(greenhouse, detection_id))


@router.get(
    "/{greenhouse_id}/{detection_id}/image",
    response_class=StreamingResponse,
    summary="Imagem analisada (ou o heatmap) vinda do Blob Storage",
    responses={
        200: {"content": {"image/jpeg": {}, "image/png": {}}},
        404: {"description": "Estufa, detecção ou imagem não encontrada"},
        502: {"description": "Falha ao ler o Blob Storage"},
        503: {"description": "Blob Storage não configurado"},
    },
)
def get_detection_image(
    greenhouse: AuthorizedGreenhouse,
    db: DbSession,
    detection_id: DetectionId,
    store: Annotated[BlobStore, Depends(get_blob_store)],
    variant: Annotated[Literal["original", "heatmap"], Query()] = "original",
):
    det = DetectionService(db).get(greenhouse, detection_id)
    ref = det.imagem_blob if variant == "original" else det.heatmap_blob
    if not ref:
        raise IMAGE_NOT_FOUND
    image = store.open_image(ref)
    headers = {
        # Imagem de uma detecção não muda; o navegador pode reaproveitar, mas só para este usuário.
        "Cache-Control": "private, max-age=86400",
        "X-Content-Type-Options": "nosniff",
    }
    if image.size is not None:
        headers["Content-Length"] = str(image.size)
    if image.etag:
        headers["ETag"] = image.etag
    return StreamingResponse(image.chunks, media_type=image.content_type, headers=headers)
