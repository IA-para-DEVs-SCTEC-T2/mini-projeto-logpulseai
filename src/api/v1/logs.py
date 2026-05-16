"""Router para endpoints de logs — GET /api/v1/logs/{id}.

Endpoint para consulta de um log pelo seu UUID.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_repository
from src.models.schemas import LogAnalysisResponse
from src.repository.base import LogRepository

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get(
    "/{log_id}",
    response_model=LogAnalysisResponse,
    summary="Consulta log por ID",
    description="Retorna os detalhes completos de um log analisado pelo seu UUID.",
    responses={
        404: {"description": "Log não encontrado"},
    },
)
async def get_log_by_id(
    log_id: str,
    repository: LogRepository = Depends(get_repository),
) -> LogAnalysisResponse:
    """Consulta um log analisado pelo seu UUID.

    Args:
        log_id: UUID do registro a ser consultado.
        repository: Instância do repositório injetada via Depends.

    Returns:
        LogAnalysisResponse com análise e diagnóstico completos.

    Raises:
        HTTPException 404: Se o log não for encontrado.
    """
    result = await repository.get_by_id(log_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log com ID '{log_id}' não encontrado",
        )
    return result
