from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.client_ip import client_ip
from app.core.config import get_settings
from app.core.rate_limit import login_ip_limiter
from app.core.security import REFRESH_COOKIE_NAME
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.auth_service import TOO_MANY_ATTEMPTS, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.jwt_refresh_ttl_days * 24 * 3600,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="strict",
        path=f"{settings.api_prefix}/auth",
    )


def _token_response(access_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token, expires_in=get_settings().jwt_access_ttl_minutes * 60
    )


@router.post("/login", response_model=TokenResponse, summary="Autenticar com e-mail e senha")
def login(data: LoginRequest, request: Request, response: Response, db: DbSession):
    if not login_ip_limiter.hit(client_ip(request)):
        raise TOO_MANY_ATTEMPTS
    _, access, refresh = AuthService(db).login(data.email, data.password)
    _set_refresh_cookie(response, refresh)
    return _token_response(access)


@router.post("/refresh", response_model=TokenResponse, summary="Renovar o access token")
def refresh(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
):
    _, access, new_refresh = AuthService(db).refresh(refresh_token)
    _set_refresh_cookie(response, new_refresh)  # rotação do refresh token
    return _token_response(access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Encerrar a sessão")
def logout(response: Response) -> Response:
    settings = get_settings()
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=f"{settings.api_prefix}/auth",
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=MeResponse, summary="Usuário autenticado")
def me(user: CurrentUser) -> MeResponse:
    return MeResponse(id=user.id, email=user.email, name=user.nome, is_admin=user.adm)
