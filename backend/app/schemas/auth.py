from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, description="E-mail do usuário")
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Validade do access token, em segundos")


class GreenhouseRef(BaseModel):
    id: int
    name: str | None


class MeResponse(BaseModel):
    id: int
    email: str
    name: str | None
    is_admin: bool
