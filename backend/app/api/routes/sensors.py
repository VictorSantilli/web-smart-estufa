from fastapi import APIRouter

from app.api.deps import AuthorizedGreenhouse, DbSession
from app.core.errors import AppError
from app.schemas.dashboard import LatestReadingResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get(
    "/{greenhouse_id}/latest",
    response_model=LatestReadingResponse,
    summary="Última leitura bruta dos sensores da estufa",
    responses={404: {"description": "Estufa sem acesso ou sem leituras"}},
)
def latest_reading(greenhouse: AuthorizedGreenhouse, db: DbSession):
    reading = DashboardService(db).latest_reading(greenhouse)
    if reading is None:
        raise AppError(404, "no_readings", "Esta estufa ainda não enviou leituras.")
    return reading
