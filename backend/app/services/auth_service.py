"""Login, renovação de sessão e bloqueio por tentativas."""

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    InvalidTokenError,
    burn_password_check,
    create_token,
    decode_token,
    verify_password,
)
from app.models import Usuario
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = AppError(401, "invalid_credentials", "E-mail ou senha inválidos.")
TOO_MANY_ATTEMPTS = AppError(
    429, "too_many_attempts", "Muitas tentativas de login. Tente novamente mais tarde."
)
SESSION_EXPIRED = AppError(401, "session_expired", "Sessão expirada. Faça login novamente.")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

    def login(self, email: str, password: str) -> tuple[Usuario, str, str]:
        """Retorna (usuário, access_token, refresh_token) ou lança AppError."""
        user = self.users.get_by_email(email)
        if user is None:
            burn_password_check(password)
            raise INVALID_CREDENTIALS

        now = utcnow()
        if user.bloqueado_ate and user.bloqueado_ate > now:
            burn_password_check(password)  # mesmo tempo de resposta de uma tentativa normal
            raise TOO_MANY_ATTEMPTS

        valid, new_hash = verify_password(password, user.senha_hash)
        if not valid:
            self._register_failure(user)
            raise INVALID_CREDENTIALS

        if not user.ativo:
            # Mesma resposta de credencial inválida: não revela que a conta existe.
            raise INVALID_CREDENTIALS

        user.tentativas_falhas = 0
        user.bloqueado_ate = None
        if new_hash:
            user.senha_hash = new_hash  # rehash transparente (ex.: bcrypt -> Argon2id)
        self.db.commit()
        return user, *self._issue_tokens(user)

    def refresh(self, refresh_token: str | None) -> tuple[Usuario, str, str]:
        if not refresh_token:
            raise SESSION_EXPIRED
        try:
            payload = decode_token(refresh_token, "refresh")
        except InvalidTokenError:
            raise SESSION_EXPIRED from None
        user = self.users.get(payload.user_id)
        if user is None or not user.ativo or user.token_versao != payload.token_version:
            raise SESSION_EXPIRED
        return user, *self._issue_tokens(user)

    def _issue_tokens(self, user: Usuario) -> tuple[str, str]:
        return (
            create_token(user.id, user.token_versao, "access"),
            create_token(user.id, user.token_versao, "refresh"),
        )

    def _register_failure(self, user: Usuario) -> None:
        user.tentativas_falhas = (user.tentativas_falhas or 0) + 1
        if user.tentativas_falhas >= self.settings.login_max_attempts:
            user.bloqueado_ate = utcnow() + timedelta(minutes=self.settings.login_lock_minutes)
            user.tentativas_falhas = 0
            logger.warning("Conta %s bloqueada por excesso de tentativas", user.id)
        self.db.commit()
