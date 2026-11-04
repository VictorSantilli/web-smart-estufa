"""Ponto de entrada do backend Smart Estufa.

- A API fica sob /api (documentação em /api/docs).
- Em produção, o mesmo processo serve o build do React (pasta FRONTEND_DIST_DIR),
  de modo que frontend e API compartilham a mesma origem.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.telemetry import configure_telemetry


def _mount_frontend(app: FastAPI, settings: Settings) -> None:
    dist = Path(settings.frontend_dist_dir)
    index = dist / "index.html"
    if not index.is_file():
        return

    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        # Rotas /api inexistentes devem responder 404 em JSON, não o index.html.
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Recurso não encontrado.")
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    # Antes de criar o FastAPI, para a instrumentação capturar as requisições.
    configure_telemetry(settings)

    docs = settings.docs_enabled
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        docs_url=f"{settings.api_prefix}/docs" if docs else None,
        redoc_url=f"{settings.api_prefix}/redoc" if docs else None,
        swagger_ui_oauth2_redirect_url=f"{settings.api_prefix}/docs/oauth2-redirect",
        openapi_url=f"{settings.api_prefix}/openapi.json" if docs else None,
    )

    app.add_middleware(
        SecurityHeadersMiddleware, hsts=settings.is_production, api_prefix=settings.api_prefix
    )
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,  # necessário para o cookie de refresh (Etapa 3)
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    register_error_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    _mount_frontend(app, settings)
    return app


app = create_app()
