"""Hash de senhas e tokens JWT.

Senhas: o pwdlib verifica bcrypt (formato atual do banco, usado pelo app mobile) e
Argon2id. Novas senhas usam o esquema de PASSWORD_HASH_SCHEME. Com "argon2id", hashes
bcrypt antigos são regravados em Argon2id no próximo login (rehash transparente).

Tokens: access token curto (no corpo da resposta, guardado só em memória no frontend) e
refresh token longo (cookie HttpOnly). Ambos carregam "tv" = Usuarios.TokenVersao:
incrementar a coluna invalida todas as sessões do usuário.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Literal

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import get_settings

TokenType = Literal["access", "refresh"]
REFRESH_COOKIE_NAME = "se_refresh"


@lru_cache
def _password_hash() -> PasswordHash:
    bcrypt, argon2 = BcryptHasher(), Argon2Hasher()
    # O primeiro hasher da tupla é o usado para gerar novos hashes.
    if get_settings().password_hash_scheme == "argon2id":
        return PasswordHash((argon2, bcrypt))
    return PasswordHash((bcrypt, argon2))


def hash_password(password: str) -> str:
    return _password_hash().hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Retorna (válida, novo_hash). novo_hash != None quando o hash deve ser regravado."""
    try:
        return _password_hash().verify_and_update(password, password_hash)
    except Exception:
        # Hash em formato desconhecido ou corrompido: trata como senha inválida.
        return False, None


# Hash fixo para gastar o mesmo tempo quando o e-mail não existe (evita enumeração por tempo).
_DUMMY_HASH: str | None = None


def burn_password_check(password: str) -> None:
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password("dummy-password-for-timing")
    verify_password(password, _DUMMY_HASH)


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    token_version: int
    type: TokenType


class InvalidTokenError(Exception):
    pass


def create_token(user_id: int, token_version: int, token_type: TokenType) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    if token_type == "access":
        expires = now + timedelta(minutes=settings.jwt_access_ttl_minutes)
    else:
        expires = now + timedelta(days=settings.jwt_refresh_ttl_days)
    payload = {
        "sub": str(user_id),
        "tv": token_version,
        "type": token_type,
        "iat": now,
        "exp": expires,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    settings = get_settings()
    try:
        data = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type", "tv"]},
        )
        if data["type"] != expected_type:
            raise InvalidTokenError("Tipo de token inválido.")
        return TokenPayload(
            user_id=int(data["sub"]), token_version=int(data["tv"]), type=data["type"]
        )
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise InvalidTokenError(str(exc)) from exc
