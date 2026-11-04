"""Dependências de autenticação e autorização.

Toda regra de acesso é decidida aqui, no backend. O frontend apenas esconde opções.
"""

from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import InvalidTokenError, decode_token
from app.database.session import get_db
from app.models import Estufa, Usuario
from app.repositories.greenhouse_repository import GreenhouseRepository
from app.repositories.user_repository import UserRepository

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)

NOT_AUTHENTICATED = AppError(401, "not_authenticated", "Autenticação necessária.")
FORBIDDEN = AppError(403, "forbidden", "Você não tem permissão para esta ação.")
# 404 (e não 403) para estufas sem permissão: não confirma que a estufa existe.
GREENHOUSE_NOT_FOUND = AppError(404, "greenhouse_not_found", "Estufa não encontrada.")


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Usuario:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise NOT_AUTHENTICATED
    try:
        payload = decode_token(credentials.credentials, "access")
    except InvalidTokenError:
        raise NOT_AUTHENTICATED from None
    user = UserRepository(db).get(payload.user_id)
    # Usuário desativado ou com TokenVersao alterada perde o acesso na hora.
    if user is None or not user.ativo or user.token_versao != payload.token_version:
        raise NOT_AUTHENTICATED
    return user


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> Usuario:
    if not user.adm:
        raise FORBIDDEN
    return user


AdminUser = Annotated[Usuario, Depends(require_admin)]


def require_greenhouse_access(
    greenhouse_id: Annotated[int, Path(ge=1)], user: CurrentUser, db: DbSession
) -> Estufa:
    """Use em toda rota com {greenhouse_id}: ADM acessa todas; usuário comum só as vinculadas."""
    if not user.adm and not UserRepository(db).has_greenhouse(user.id, greenhouse_id):
        raise GREENHOUSE_NOT_FOUND
    greenhouse = GreenhouseRepository(db).get(greenhouse_id)
    if greenhouse is None:
        raise GREENHOUSE_NOT_FOUND
    return greenhouse


AuthorizedGreenhouse = Annotated[Estufa, Depends(require_greenhouse_access)]
