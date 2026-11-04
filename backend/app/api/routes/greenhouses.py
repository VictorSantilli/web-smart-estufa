from fastapi import APIRouter

from app.api.deps import AdminUser, AuthorizedGreenhouse, CurrentUser, DbSession
from app.schemas.dashboard import DeviceOut
from app.schemas.greenhouse import GreenhouseOut, GreenhouseUserOut
from app.services.dashboard_service import DashboardService
from app.services.greenhouse_service import GreenhouseService

router = APIRouter(prefix="/greenhouses", tags=["greenhouses"])


@router.get("", response_model=list[GreenhouseOut], summary="Estufas que o usuário pode ver")
def list_greenhouses(user: CurrentUser, db: DbSession):
    return GreenhouseService(db).list_for(user)


@router.get("/{greenhouse_id}", response_model=GreenhouseOut, summary="Detalhar estufa")
def get_greenhouse(greenhouse: AuthorizedGreenhouse):
    return GreenhouseOut(id=greenhouse.id, name=greenhouse.nome)


@router.get(
    "/{greenhouse_id}/users",
    response_model=list[GreenhouseUserOut],
    summary="Usuários com acesso à estufa (ADM)",
)
def greenhouse_users(greenhouse: AuthorizedGreenhouse, _: AdminUser, db: DbSession):
    return GreenhouseService(db).users_with_access(greenhouse.id)


@router.get(
    "/{greenhouse_id}/devices",
    response_model=list[DeviceOut],
    summary="Dispositivos (ESP32) da estufa e último contato",
)
def greenhouse_devices(greenhouse: AuthorizedGreenhouse, db: DbSession):
    return DashboardService(db).devices(greenhouse)
