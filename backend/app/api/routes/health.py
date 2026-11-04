from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.database.session import ping_database
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", summary="O processo está no ar (sem consultar o banco)")
def live() -> dict[str, str]:
    """Usado pelas sondas de liveness/readiness do Container Apps.

    Não depende do banco: se o Azure SQL estiver pausado ou fora do ar, o container não é
    reiniciado em loop e a API continua respondendo com erros claros.
    """
    return {"status": "ok"}


@router.get("/health", response_model=HealthResponse, summary="Saúde da aplicação e do banco")
def health(response: Response) -> HealthResponse:
    settings = get_settings()
    db_ok = ping_database()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="ok" if db_ok else "unavailable",
        version=settings.app_version,
        environment=settings.app_env,
    )
