"""Formato padronizado de erro: {"detail": {"code": str, "message": str, "fields"?: [...]}}.

Nunca devolve stack trace nem mensagens do banco para o cliente.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Erro de negócio com código estável, tratado pelo handler abaixo."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _body(code: str, message: str, **extra: object) -> dict:
    return {"detail": {"code": code, "message": message, **extra}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))

    @app.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            content = {"detail": exc.detail}
        else:
            phrase = HTTPStatus(exc.status_code).phrase
            code = phrase.lower().replace(" ", "_")
            message = exc.detail if isinstance(exc.detail, str) else phrase
            content = _body(code, message)
        return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body("validation_error", "Dados inválidos.", fields=fields),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=_body("internal_error", "Erro interno."))
