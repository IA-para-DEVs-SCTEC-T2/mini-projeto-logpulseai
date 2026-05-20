"""Rotas de logs da API v1 do LogPulse IA (View layer).

Define apenas as rotas HTTP e delega toda a lógica ao LogsController.
Padrão MVC: Route (View) → Controller → Service → Repository (Model).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, UploadFile, status

from src.ai.base import AIEngine
from src.analyzer.base import LogAnalyzer
from src.api.v1.controllers.logs_controller import LogsController
from src.core.dependencies import get_ai_engine, get_analyzer, get_parser, get_repository
from src.models.schemas import (
    LogAnalysisResponse,
    LogListResponse,
    LogTextUpload,
)
from src.parsers.base import LogParser
from src.repository.base import LogRepository
from src.services.log_analysis_service import LogAnalysisService
from src.services.log_storage_service import LogStorageService

router = APIRouter()


def _build_controller(
    parser: LogParser,
    analyzer: LogAnalyzer,
    ai_engine: AIEngine,
    repository: LogRepository,
) -> LogsController:
    """Constrói o controller com services configurados.

    Monta a cadeia MVC completa:
    Controller → Services → Repository/Parser/Analyzer/AI
    """
    analysis_service = LogAnalysisService(
        parser=parser,
        analyzer=analyzer,
        ai_engine=ai_engine,
        repository=repository,
    )
    storage_service = LogStorageService(repository=repository)
    return LogsController(
        analysis_service=analysis_service,
        storage_service=storage_service,
    )


def _build_storage_controller(repository: LogRepository) -> LogsController:
    """Constrói controller apenas com storage service (para operações CRUD).

    Usado por endpoints que não precisam do pipeline de análise.
    """
    storage_service = LogStorageService(repository=repository)
    return LogsController(
        analysis_service=None,  # type: ignore[arg-type]
        storage_service=storage_service,
    )


@router.post(
    "/file",
    response_model=LogAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envio de log via arquivo",
)
async def upload_log_file(
    file: UploadFile,
    parser: Annotated[LogParser, Depends(get_parser)],
    analyzer: Annotated[LogAnalyzer, Depends(get_analyzer)],
    ai_engine: Annotated[AIEngine, Depends(get_ai_engine)],
    repo: Annotated[LogRepository, Depends(get_repository)],
) -> LogAnalysisResponse:
    """Processa upload de arquivo de log (.log ou .txt)."""
    controller = _build_controller(parser, analyzer, ai_engine, repo)
    return await controller.upload_file(file)


@router.post(
    "/text",
    response_model=LogAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envio de log via texto",
)
async def upload_log_text(
    payload: Annotated[LogTextUpload, Body(embed=False)],
    parser: Annotated[LogParser, Depends(get_parser)],
    analyzer: Annotated[LogAnalyzer, Depends(get_analyzer)],
    ai_engine: Annotated[AIEngine, Depends(get_ai_engine)],
    repo: Annotated[LogRepository, Depends(get_repository)],
) -> LogAnalysisResponse:
    """Processa envio de log via texto puro."""
    controller = _build_controller(parser, analyzer, ai_engine, repo)
    return await controller.upload_text(payload)


@router.get(
    "/",
    response_model=LogListResponse,
    summary="Listagem paginada de logs",
)
async def list_logs(
    page: int = 1,
    page_size: int = 20,
    repo: LogRepository = Depends(get_repository),
) -> LogListResponse:
    """Lista logs com paginação."""
    controller = _build_storage_controller(repo)
    return await controller.list_logs(page, page_size)


@router.get(
    "/{log_id}",
    response_model=LogAnalysisResponse,
    summary="Consulta log por ID",
    responses={
        404: {"description": "Log não encontrado"},
        422: {"description": "UUID inválido"}
    },
)
async def get_log_by_id(
    log_id: UUID,
    repo: LogRepository = Depends(get_repository),
) -> LogAnalysisResponse:
    """Recupera um log pelo ID (UUID).
    
    Args:
        log_id: UUID do log no formato padrão (ex: 550e8400-e29b-41d4-a716-446655440000)
        
    Returns:
        Dados completos do log com análise e diagnóstico
        
    Raises:
        422: Se o UUID fornecido for inválido
        404: Se o log não for encontrado
    """
    controller = _build_storage_controller(repo)
    return await controller.get_by_id(str(log_id))


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remoção de log pelo ID",
    responses={
        404: {"description": "Log não encontrado"},
        422: {"description": "UUID inválido"}
    },
)
async def delete_log(
    log_id: UUID,
    repo: LogRepository = Depends(get_repository),
) -> None:
    """Remove um log pelo ID (UUID).
    
    Args:
        log_id: UUID do log no formato padrão (ex: 550e8400-e29b-41d4-a716-446655440000)
        
    Returns:
        Status 204 (No Content) em caso de sucesso
        
    Raises:
        422: Se o UUID fornecido for inválido
        404: Se o log não for encontrado
    """
    controller = _build_storage_controller(repo)
    await controller.delete(str(log_id))
