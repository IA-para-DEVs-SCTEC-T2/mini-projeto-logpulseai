"""Testes para o módulo de injeção de dependências do LogPulse IA."""

from __future__ import annotations

import os

import pytest

from src.ai.base import AIEngine
from src.ai.ollama_engine import OllamaAIEngine
from src.analyzer.base import LogAnalyzer
from src.analyzer.detector import AnomalyDetector
from src.core.config import Settings
from src.core.dependencies import get_ai_engine, get_analyzer, get_parser, get_repository
from src.parsers.base import LogParser
from src.parsers.drain3_parser import Drain3LogParser
from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository


class TestGetParser:
    """Testes para a dependência get_parser."""

    def test_accepts_custom_settings(self) -> None:
        """Verifica que aceita Settings customizado."""
        settings = Settings(drain_depth=6, drain_sim_th=0.5)
        parser = get_parser(settings=settings)
        assert isinstance(parser, Drain3LogParser)


class TestGetAnalyzer:
    """Testes para a dependência get_analyzer."""

    def test_accepts_custom_settings(self) -> None:
        """Verifica que aceita Settings customizado."""
        settings = Settings(spike_threshold=20, spike_window_seconds=120)
        analyzer = get_analyzer(settings=settings)
        assert isinstance(analyzer, AnomalyDetector)


class TestGetAIEngine:
    """Testes para a dependência get_ai_engine."""

    def test_accepts_custom_settings(self) -> None:
        """Verifica que aceita Settings customizado."""
        settings = Settings(ollama_model="llama3.1")
        engine = get_ai_engine(settings=settings)
        assert isinstance(engine, OllamaAIEngine)


class TestGetRepository:
    """Testes para a dependência get_repository."""

    @pytest.mark.asyncio
    async def test_returns_log_repository(self, tmp_path: object) -> None:
        """Verifica que retorna instância de LogRepository."""
        db_file = os.path.join(str(tmp_path), "test.db")
        settings = Settings(database_url=db_file)
        async for repo in get_repository(settings=settings):
            assert isinstance(repo, LogRepository)

    @pytest.mark.asyncio
    async def test_returns_sqlite_repository(self, tmp_path: object) -> None:
        """Verifica que a implementação concreta é SQLiteLogRepository."""
        db_file = os.path.join(str(tmp_path), "test.db")
        settings = Settings(database_url=db_file)
        async for repo in get_repository(settings=settings):
            assert isinstance(repo, SQLiteLogRepository)

    @pytest.mark.asyncio
    async def test_repository_is_initialized(self, tmp_path: object) -> None:
        """Verifica que o repositório é inicializado (tabelas criadas)."""
        db_file = os.path.join(str(tmp_path), "test.db")
        settings = Settings(database_url=db_file)
        async for repo in get_repository(settings=settings):
            # Se inicializado, operações CRUD devem funcionar
            items = await repo.list_paginated(page=1, page_size=10)
            assert items == []
