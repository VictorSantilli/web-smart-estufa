from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Formato padrão de erro devolvido por toda a API."""

    detail: ErrorDetail
