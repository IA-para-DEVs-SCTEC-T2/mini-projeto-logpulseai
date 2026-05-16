"""Router para endpoints de logs — GET /api/v1/logs/{id}.

Endpoint para consulta de um log pelo seu UUID.
"""Endpoints de logs da API v1 do LogPulse IA.

Implementa os endpoints CRUD e de análise de logs com injeção
de dependências via FastAPI Depends.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_repository
from src.models.schemas import LogAnalysisResponse
from src.repository.base import LogRepository

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.ai.base import AIEngine
from src.analyzer.base import LogAnalyzer
from src.core.dependencies import get_ai_engine, get_analyzer, get_parser, get_repository
from src.models.schemas import (
    LogAnalysisResponse,
    LogListResponse,
    LogTextUpload,
)
from src.parsers.base import LogParser
from src.repository.base import LogRepository

router = APIRouter()


@router.post(
    "/file",
    response_model=LogAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envio de log via arquivo",
    description="Recebe um arquivo .log ou .txt e retorna análise com diagnóstico IA.",
)
async def upload_log_file(
    file: UploadFile,
    parser: Annotated[LogParser, Depends(get_parser)],
    analyzer: Annotated[LogAnalyzer, Depends(get_analyzer)],
    ai_engine: Annotated[AIEngine, Depends(get_ai_engine)],
    repo: Annotated[LogRepository, Depends(get_repository)],
) -> LogAnalysisResponse:
    """Processa upload de arquivo de log.

    Args:
        file: Arquivo .log ou .txt enviado pelo usuário.
        parser: Parser de logs injetado.
        analyzer: Analyzer de anomalias injetado.
        ai_engine: Motor de IA injetado.
        repo: Repositório de logs injetado.

    Returns:
        Resposta com análise e diagnóstico persistidos.

    Raises:
        HTTPException 400: Se o arquivo não for .log ou .txt.
        HTTPException 422: Se o conteúdo for inválido.
    """
    # Valida extensão
    filename = file.filename or ""
    if not filename.lower().endswith((".log", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .log e .txt são aceitos.",
        )

    content = (await file.read()).decode("utf-8", errors="replace")
    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo vazio ou sem conteúdo válido.",
        )

    # Pipeline: parse → analyze → diagnose → persist
    entries = parser.parse(content)
    templates = parser.get_templates()
    analysis = analyzer.analyze(entries, templates)
    diagnosis = ai_engine.diagnose(analysis, entries)
    log_id = await repo.create(content, analysis, diagnosis)

    record = await repo.get_by_id(log_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao recuperar registro após criação.",
        )
    return record


@router.post(
    "/text",
    response_model=LogAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envio de log via texto",
    description="Recebe conteúdo de log em texto puro e retorna análise com diagnóstico IA.",
)
async def upload_log_text(
    payload: LogTextUpload,
    parser: Annotated[LogParser, Depends(get_parser)],
    analyzer: Annotated[LogAnalyzer, Depends(get_analyzer)],
    ai_engine: Annotated[AIEngine, Depends(get_ai_engine)],
    repo: Annotated[LogRepository, Depends(get_repository)],
) -> LogAnalysisResponse:
    """Processa envio de log via texto.

    Args:
        payload: Conteúdo do log em texto puro.
        parser: Parser de logs injetado.
        analyzer: Analyzer de anomalias injetado.
        ai_engine: Motor de IA injetado.
        repo: Repositório de logs injetado.

    Returns:
        Resposta com análise e diagnóstico persistidos.
    """
    entries = parser.parse(payload.content)
    templates = parser.get_templates()
    analysis = analyzer.analyze(entries, templates)
    diagnosis = ai_engine.diagnose(analysis, entries)
    log_id = await repo.create(payload.content, analysis, diagnosis)

    record = await repo.get_by_id(log_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao recuperar registro após criação.",
        )
    return record


@router.get(
    "",
    response_model=LogListResponse,
    summary="Listagem paginada de logs",
    description="Retorna logs analisados com paginação.",
)
async def list_logs(
    page: int = 1,
    page_size: int = 20,
    repo: LogRepository = Depends(get_repository),
) -> LogListResponse:
    """Lista logs com paginação.

    Args:
        page: Número da página (começa em 1).
        page_size: Itens por página (máx. 100).
        repo: Repositório de logs injetado.

    Returns:
        Lista paginada de logs analisados.
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    items = await repo.list_paginated(page, page_size)

    # Calcula total (simplificado — em produção usar COUNT query)
    # Por ora retorna baseado nos itens retornados
    total = len(items) + ((page - 1) * page_size)
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return LogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


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
    summary="Consulta de log pelo ID",
    description="Retorna um log analisado pelo seu UUID.",
)
async def get_log(
    log_id: str,
    repo: LogRepository = Depends(get_repository),
) -> LogAnalysisResponse:
    """Recupera um log pelo ID.

    Args:
        log_id: UUID do registro.
        repo: Repositório de logs injetado.

    Returns:
        Log analisado com diagnóstico.

    Raises:
        HTTPException 404: Se o log não for encontrado.
    """
    record = await repo.get_by_id(log_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log '{log_id}' não encontrado.",
        )
    return record


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remoção de log pelo ID",
    description="Remove um log analisado pelo seu UUID.",
)
async def delete_log(
    log_id: str,
    repo: LogRepository = Depends(get_repository),
) -> None:
    """Remove um log pelo ID.

    Args:
        log_id: UUID do registro a remover.
        repo: Repositório de logs injetado.

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
    deleted = await repo.delete(log_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log '{log_id}' não encontrado.",
        )
