from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import AdminUser, DbSession
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserGreenhousesUpdate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

UserId = Annotated[int, Path(ge=1)]


@router.get("", response_model=Page[UserOut], summary="Listar usuários (ADM)")
def list_users(
    _: AdminUser,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100, description="Busca por nome ou e-mail")] = None,
    active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return UserService(db).list_users(search=q, active=active, page=page, page_size=page_size)


@router.post(
    "", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Cadastrar (ADM)"
)
def create_user(data: UserCreate, _: AdminUser, db: DbSession):
    return UserService(db).create(data)


@router.get("/{user_id}", response_model=UserOut, summary="Detalhar usuário (ADM)")
def get_user(user_id: UserId, _: AdminUser, db: DbSession):
    return UserService(db).get(user_id)


@router.patch("/{user_id}", response_model=UserOut, summary="Editar usuário (ADM)")
def update_user(user_id: UserId, data: UserUpdate, admin: AdminUser, db: DbSession):
    return UserService(db).update(user_id, data, admin)


@router.post("/{user_id}/deactivate", response_model=UserOut, summary="Desativar (ADM)")
def deactivate_user(user_id: UserId, admin: AdminUser, db: DbSession):
    return UserService(db).set_active(user_id, False, admin)


@router.post("/{user_id}/activate", response_model=UserOut, summary="Reativar (ADM)")
def activate_user(user_id: UserId, admin: AdminUser, db: DbSession):
    return UserService(db).set_active(user_id, True, admin)


@router.put(
    "/{user_id}/greenhouses", response_model=UserOut, summary="Definir estufas do usuário (ADM)"
)
def set_user_greenhouses(user_id: UserId, data: UserGreenhousesUpdate, _: AdminUser, db: DbSession):
    return UserService(db).set_greenhouses(user_id, data.greenhouse_ids)
