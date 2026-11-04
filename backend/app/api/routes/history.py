from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.api.deps import AuthorizedGreenhouse, DbSession
from app.schemas.history import HistoryResponse
from app.services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get(
    "/{greenhouse_id}",
    response_model=HistoryResponse,
    summary="Histórico de temperatura e umidade da estufa",
    description=(
        "Use `period` (24h, 7d ou 30d) **ou** `start` e `end` (datas no fuso do projeto, "
        "inclusivas, no máximo HISTORY_MAX_DAYS dias). Sem parâmetros, devolve as últimas 24 h."
    ),
    responses={404: {"description": "Estufa sem acesso"}, 422: {"description": "Período inválido"}},
)
def get_history(
    greenhouse: AuthorizedGreenhouse,
    db: DbSession,
    period: Annotated[Literal["24h", "7d", "30d"] | None, Query()] = None,
    start: Annotated[date | None, Query(description="Data inicial (AAAA-MM-DD)")] = None,
    end: Annotated[date | None, Query(description="Data final (AAAA-MM-DD)")] = None,
):
    return HistoryService(db).history(greenhouse, period, start, end)
