"""Endpoints de logs da API v1 do LogPulse IA."""

from __future__ import annotations

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


@router.post("/file", response_model=LogAnalysisResponse, status_code=status.HTTP_201_CREATED,
             summary="Envio de log via arquivo")
async def upload_log_file(
    file: UploadFile,
    parser: Annotated[LogParser, Depends(get_parser)],
    analyzer: Annotated[LogAnalyzer, Depends(get_analyzer)],
    ai_engine: Annotated[AIEngine, Depends(get_ai_engine)],
    repo: Annotated[LogRepository, Depends(get_repository)],
) -> LogAnalysisResponse:
    """Processa upload de arquivo de log (.log ou .txt)."""
    filename = file.filename or ""
    if not filename.lower().endswith((".log", ".txt")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Apenas arquivos .log e .txt são aceitos.")
    content = (await file.read()).decode("utf-8", errors="replace")
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Arquivo vazio ou sem conteúdo válido.")
    entries = parser.parse(content)
    templates = parser.get_templates()
    analysis = analyzer.analyze(entries, templates)
    diagnosis = ai_engine.diagnose(analysis, entries)
    log_id = await repo.create(content, analysis, diagnosis)
    record = await repo.get_by_id(log_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Falha ao recuperar registro após criação.")
    return record


@router.post("/text", response_model=LogAnalysisResponse, status_code=status.HTTP_201_CREATED,
             summary="Envio de log via texto")
async def upload_log_text(
    payload: LogTextUpload,
    parser: Annotated[LogParser, Depends(get_parser)],
    analyzer: Annotated[LogAnalyzer, Depends(get_analyzer)],
    ai_engine: Annotated[AIEngine, Depends(get_ai_engine)],
    repo: Annotated[LogRepository, Depends(get_repository)],
) -> LogAnalysisResponse:
    """Processa envio de log via texto puro."""
    entries = parser.parse(payload.content)
    templates = parser.get_templates()
    analysis = analyzer.analyze(entries, templates)
    diagnosis = ai_engine.diagnose(analysis, entries)
    log_id = await repo.create(payload.content, analysis, diagnosis)
    record = await repo.get_by_id(log_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Falha ao recuperar registro após criação.")
    return record


@router.get("/", response_model=LogListResponse, summary="Listagem paginada de logs")
async def list_logs(
    page: int = 1,
    page_size: int = 20,
    repo: LogRepository = Depends(get_repository),
) -> LogListResponse:
    """Lista logs com paginação."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    items = await repo.list_paginated(page, page_size)
    total = len(items) + ((page - 1) * page_size)
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    return LogListResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{log_id}", response_model=LogAnalysisResponse, summary="Consulta log por ID",
            responses={404: {"description": "Log não encontrado"}})
async def get_log_by_id(
    log_id: str,
    repo: LogRepository = Depends(get_repository),
) -> LogAnalysisResponse:
    """Recupera um log pelo ID."""
    record = await repo.get_by_id(log_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Log '{log_id}' não encontrado.")
    return record


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remoção de log pelo ID")
async def delete_log(
    log_id: str,
    repo: LogRepository = Depends(get_repository),
) -> None:
    """Remove um log pelo ID."""
    deleted = await repo.delete(log_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Log '{log_id}' não encontrado.")
