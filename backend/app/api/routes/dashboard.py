from fastapi import APIRouter

from app.api.deps import AuthorizedGreenhouse, DbSession
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/{greenhouse_id}",
    response_model=DashboardResponse,
    summary="Indicadores do Dashboard da estufa",
)
def get_dashboard(greenhouse: AuthorizedGreenhouse, db: DbSession):
    return DashboardService(db).dashboard(greenhouse)
