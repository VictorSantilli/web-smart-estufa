import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.auth import GreenhouseRef

# O bcrypt (formato usado pelo app mobile) considera só os primeiros 72 bytes da senha:
# acima disso, senhas diferentes com o mesmo início seriam aceitas. Por isso o limite.
PASSWORD_MAX_BYTES = 72
PASSWORD_RULE = "A senha deve ter de 8 a 72 caracteres, com pelo menos uma letra e um número."


def _check_password(value: str) -> str:
    if (
        len(value) < 8
        or len(value.encode("utf-8")) > PASSWORD_MAX_BYTES
        or not re.search(r"[A-Za-z]", value)
        or not re.search(r"\d", value)
    ):
        raise ValueError(PASSWORD_RULE)
    return value


class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=255)
    name: str = Field(min_length=2, max_length=255)
    password: str
    is_admin: bool = False
    greenhouse_ids: list[int] = Field(default_factory=list)

    _password = field_validator("password")(_check_password)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class UserUpdate(BaseModel):
    """Campos opcionais: só os enviados são alterados."""

    email: EmailStr | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = None
    is_admin: bool | None = None

    @field_validator("password")
    @classmethod
    def _password(cls, value: str | None) -> str | None:
        return None if value is None else _check_password(value)


class UserGreenhousesUpdate(BaseModel):
    greenhouse_ids: list[int] = Field(description="Lista completa das estufas do usuário")


class UserOut(BaseModel):
    id: int
    email: str
    name: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime
    greenhouses: list[GreenhouseRef]
