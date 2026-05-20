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
from src.core.config import get_settings
from src.parsers.base import LogParser
from src.parsers.drain3_parser import Drain3LogParser
from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository


def get_parser() -> LogParser:
    """Fornece instância do parser de logs.

    Cria um Drain3LogParser configurado. Cada chamada retorna uma
    nova instância para evitar estado compartilhado entre requests.

    Returns:
        Instância de LogParser (Drain3LogParser).
    """
    return Drain3LogParser()


def get_analyzer() -> LogAnalyzer:
    """Fornece instância do analyzer de anomalias.

    Returns:
        Instância de LogAnalyzer (AnomalyDetector).
    """
    return AnomalyDetector()


def get_ai_engine() -> AIEngine:
    """Fornece instância do motor de IA.

    Cria um OllamaAIEngine configurado com URL, modelo e timeout
    definidos nas configurações da aplicação.

    Returns:
        Instância de AIEngine (OllamaAIEngine).
    """
    settings = get_settings()
    return OllamaAIEngine(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout,
    )


async def get_repository() -> AsyncGenerator[LogRepository, None]:
    """Fornece instância do repositório de logs com inicialização.

    Cria um SQLiteLogRepository, inicializa o banco de dados (cria
    tabelas se necessário) e fornece a instância para o endpoint.

    Yields:
        Instância de LogRepository (SQLiteLogRepository) inicializada.
    """
    settings = get_settings()
    repo = SQLiteLogRepository(db_path=settings.database_url)
    await repo.initialize()
    yield repo
