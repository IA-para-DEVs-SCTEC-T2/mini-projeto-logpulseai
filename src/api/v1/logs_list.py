"""Router para endpoint GET /api/v1/logs.

Endpoint para listagem paginada de logs analisados.
"""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_repository
from src.models.schemas import LogListResponse
from src.repository.base import LogRepository

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get(
    "",
    response_model=LogListResponse,
    summary="Listagem paginada de logs",
    description="Retorna logs analisados com paginação, ordenados por data de criação (mais recente primeiro).",
)
async def list_logs(
    page: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Itens por página (máx. 100)"
    ),
    repository: LogRepository = Depends(get_repository),
) -> LogListResponse:
    """Lista logs analisados com paginação.

    Args:
        page: Número da página (começa em 1).
        page_size: Quantidade de itens por página (1 a 100).
        repository: Instância do repositório injetada via Depends.

    Returns:
        LogListResponse com itens da página, total e metadados de paginação.
    """
    total = await repository.count()
    pages = math.ceil(total / page_size) if total > 0 else 0
    items = await repository.list_paginated(page, page_size)

    return LogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
