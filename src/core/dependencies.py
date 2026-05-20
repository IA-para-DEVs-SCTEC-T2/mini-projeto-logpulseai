"""Injeção de dependências do FastAPI para o LogPulse IA.

Define funções de dependência que fornecem instâncias configuradas
dos componentes do sistema (parser, analyzer, AI engine, repository).
Segue o padrão Dependency Inversion — endpoints dependem de abstrações.

Example:
    >>> from fastapi import Depends
    >>> from src.core.dependencies import get_repository
    >>>
    >>> @router.get("/logs/{log_id}")
    ... async def get_log(
    ...     log_id: str,
    ...     repo: LogRepository = Depends(get_repository),
    ... ):
    ...     return await repo.get_by_id(log_id)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from src.ai.base import AIEngine
from src.ai.ollama_engine import OllamaAIEngine
from src.analyzer.base import LogAnalyzer
from src.analyzer.detector import AnomalyDetector
from src.core.config import Settings, get_settings
from src.parsers.base import LogParser
from src.parsers.drain3_parser import Drain3LogParser
from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository


def get_parser(settings: Settings = None) -> LogParser:  # type: ignore[assignment]
    """Fornece instância do parser de logs.

    Cria um Drain3LogParser configurado. Cada chamada retorna uma
    nova instância para evitar estado compartilhado entre requests.

    Args:
        settings: Configurações da aplicação (injetado via FastAPI).

    Returns:
        Instância de LogParser (Drain3LogParser).
    """
    if settings is None:
        settings = get_settings()
    return Drain3LogParser()


def get_analyzer(settings: Settings = None) -> LogAnalyzer:  # type: ignore[assignment]
    """Fornece instância do analyzer de anomalias.

    Cria um AnomalyDetector configurado com os thresholds definidos
    nas configurações da aplicação.

    Args:
        settings: Configurações da aplicação (injetado via FastAPI).

    Returns:
        Instância de LogAnalyzer (AnomalyDetector).
    """
    if settings is None:
        settings = get_settings()
    return AnomalyDetector()


def get_ai_engine(settings: Settings = None) -> AIEngine:  # type: ignore[assignment]
    """Fornece instância do motor de IA.

    Cria um OllamaAIEngine configurado com URL e modelo definidos
    nas configurações da aplicação.

    Args:
        settings: Configurações da aplicação (injetado via FastAPI).

    Returns:
        Instância de AIEngine (OllamaAIEngine).
    """
    if settings is None:
        settings = get_settings()
    return OllamaAIEngine(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout,
    )


async def get_repository(
    settings: Settings = None,  # type: ignore[assignment]
) -> AsyncGenerator[LogRepository, None]:
    """Fornece instância do repositório de logs com inicialização.

    Cria um SQLiteLogRepository, inicializa o banco de dados (cria
    tabelas se necessário) e fornece a instância para o endpoint.

    Args:
        settings: Configurações da aplicação (injetado via FastAPI).

    Yields:
        Instância de LogRepository (SQLiteLogRepository) inicializada.
    """
    if settings is None:
        settings = get_settings()
    repo = SQLiteLogRepository(db_path=settings.database_url)
    await repo.initialize()
    yield repo
