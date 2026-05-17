"""Testes para LogAnalysisService — pipeline completo de análise.

Cobre orquestração Parser → Analyzer → AIEngine → Repository,
tratamento de erros e transação atômica.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions import (
    AIEngineError,
    AIEngineTimeoutError,
    AIEngineUnavailableError,
    AnalysisError,
    ParsingError,
    StorageError,
)
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
    LogEntry,
    LogTemplate,
    SeverityLevel,
)
from src.services.log_analysis_service import LogAnalysisService


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------


def _make_entry(severity: SeverityLevel = SeverityLevel.ERROR) -> LogEntry:
    """Cria uma LogEntry de teste."""
    return LogEntry(
        raw_content="2024-01-15 ERROR: test message",
        severity=severity,
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        message="test message",
    )


def _make_analysis_result() -> AnalysisResult:
    """Cria um AnalysisResult de teste."""
    return AnalysisResult(
        total_entries=5,
        error_count=3,
        warning_count=1,
        severity_distribution={SeverityLevel.ERROR: 3, SeverityLevel.WARNING: 1, SeverityLevel.INFO: 1},
    )


def _make_diagnosis() -> AIDiagnosis:
    """Cria um AIDiagnosis de teste."""
    return AIDiagnosis(
        summary="Problema de conexão detectado.",
        probable_cause="Pool de conexões esgotado.",
        hypotheses=[
            Hypothesis(description="H1", probability="alta", action="Verificar pool"),
            Hypothesis(description="H2", probability="média", action="Verificar rede"),
            Hypothesis(description="H3", probability="baixa", action="Verificar DNS"),
        ],
        suggested_fix="Aumentar max_connections.",
        confidence=0.85,
    )


def _make_response(log_id: str = "uuid-123") -> LogAnalysisResponse:
    """Cria um LogAnalysisResponse de teste."""
    return LogAnalysisResponse(
        id=log_id,
        analysis=_make_analysis_result(),
        diagnosis=_make_diagnosis(),
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        total_entries=5,
        summary="Problema de conexão detectado.",
    )


@pytest.fixture
def mock_parser() -> MagicMock:
    """Parser mock que retorna entradas válidas."""
    parser = MagicMock()
    parser.parse.return_value = [_make_entry() for _ in range(5)]
    parser.get_templates.return_value = [
        LogTemplate(template_id="1", pattern="ERROR: <*>", occurrences=5)
    ]
    return parser


@pytest.fixture
def mock_analyzer() -> MagicMock:
    """Analyzer mock que retorna resultado válido."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = _make_analysis_result()
    return analyzer


@pytest.fixture
def mock_ai_engine() -> MagicMock:
    """AIEngine mock que retorna diagnóstico válido."""
    engine = MagicMock()
    engine.diagnose.return_value = _make_diagnosis()
    return engine


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Repository mock com operações assíncronas."""
    repo = AsyncMock()
    repo.create.return_value = "uuid-123"
    repo.get_by_id.return_value = _make_response()
    return repo


@pytest.fixture
def service(
    mock_parser: MagicMock,
    mock_analyzer: MagicMock,
    mock_ai_engine: MagicMock,
    mock_repository: AsyncMock,
) -> LogAnalysisService:
    """Instância do serviço com todas as dependências mockadas."""
    return LogAnalysisService(
        parser=mock_parser,
        analyzer=mock_analyzer,
        ai_engine=mock_ai_engine,
        repository=mock_repository,
    )


# ---------------------------------------------------------------------------
# Testes do pipeline completo
# ---------------------------------------------------------------------------


class TestAnalyzeContent:
    """Testes para LogAnalysisService.analyze_content()."""

    @pytest.mark.asyncio
    async def test_pipeline_completo_sucesso(
        self,
        service: LogAnalysisService,
        mock_parser: MagicMock,
        mock_analyzer: MagicMock,
        mock_ai_engine: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Pipeline completo executa todas as etapas na ordem correta."""
        content = "2024-01-15 ERROR: connection timeout"

        result = await service.analyze_content(content)

        # Verifica que todas as etapas foram chamadas
        mock_parser.parse.assert_called_once_with(content)
        mock_parser.get_templates.assert_called_once()
        mock_analyzer.analyze.assert_called_once()
        mock_ai_engine.diagnose.assert_called_once()
        mock_repository.create.assert_called_once()
        mock_repository.get_by_id.assert_called_once_with("uuid-123")

        assert isinstance(result, LogAnalysisResponse)
        assert result.id == "uuid-123"

    @pytest.mark.asyncio
    async def test_pipeline_retorna_response_completo(
        self, service: LogAnalysisService
    ) -> None:
        """Pipeline retorna LogAnalysisResponse com todos os campos."""
        result = await service.analyze_content("ERROR: test")

        assert result.id == "uuid-123"
        assert result.analysis.total_entries == 5
        assert result.diagnosis.summary == "Problema de conexão detectado."
        assert result.total_entries == 5

    @pytest.mark.asyncio
    async def test_transacao_atomica_nao_persiste_se_ai_falha(
        self,
        mock_parser: MagicMock,
        mock_analyzer: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Não persiste no repositório se AIEngine falhar."""
        engine = MagicMock()
        engine.diagnose.side_effect = AIEngineTimeoutError("Timeout")

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=mock_analyzer,
            ai_engine=engine,
            repository=mock_repository,
        )

        with pytest.raises(AIEngineTimeoutError):
            await service.analyze_content("ERROR: test")

        # Repository.create NÃO deve ter sido chamado
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_transacao_atomica_nao_persiste_se_analyzer_falha(
        self,
        mock_parser: MagicMock,
        mock_ai_engine: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Não persiste no repositório se Analyzer falhar."""
        analyzer = MagicMock()
        analyzer.analyze.side_effect = AnalysisError("Falha na análise")

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=analyzer,
            ai_engine=mock_ai_engine,
            repository=mock_repository,
        )

        with pytest.raises(AnalysisError):
            await service.analyze_content("ERROR: test")

        mock_repository.create.assert_not_called()


# ---------------------------------------------------------------------------
# Testes de tratamento de erros
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Testes para tratamento de erros com exceções customizadas."""

    @pytest.mark.asyncio
    async def test_parsing_error_quando_parser_falha(
        self,
        mock_analyzer: MagicMock,
        mock_ai_engine: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Lança ParsingError quando parser lança exceção."""
        parser = MagicMock()
        parser.parse.side_effect = Exception("Parse failed")

        service = LogAnalysisService(
            parser=parser,
            analyzer=mock_analyzer,
            ai_engine=mock_ai_engine,
            repository=mock_repository,
        )

        with pytest.raises(ParsingError) as exc_info:
            await service.analyze_content("invalid content")

        assert "Parse failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parsing_error_quando_nenhuma_entrada_valida(
        self,
        mock_analyzer: MagicMock,
        mock_ai_engine: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Lança ParsingError quando parser retorna lista vazia."""
        parser = MagicMock()
        parser.parse.return_value = []  # Nenhuma entrada válida

        service = LogAnalysisService(
            parser=parser,
            analyzer=mock_analyzer,
            ai_engine=mock_ai_engine,
            repository=mock_repository,
        )

        with pytest.raises(ParsingError) as exc_info:
            await service.analyze_content("empty content")

        assert "Nenhuma entrada" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analysis_error_quando_analyzer_falha(
        self,
        mock_parser: MagicMock,
        mock_ai_engine: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """Lança AnalysisError quando analyzer lança exceção genérica."""
        analyzer = MagicMock()
        analyzer.analyze.side_effect = RuntimeError("Unexpected error")

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=analyzer,
            ai_engine=mock_ai_engine,
            repository=mock_repository,
        )

        with pytest.raises(AnalysisError) as exc_info:
            await service.analyze_content("ERROR: test")

        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ai_engine_unavailable_propagada(
        self,
        mock_parser: MagicMock,
        mock_analyzer: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """AIEngineUnavailableError é propagada sem wrapping."""
        engine = MagicMock()
        engine.diagnose.side_effect = AIEngineUnavailableError("Ollama offline")

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=mock_analyzer,
            ai_engine=engine,
            repository=mock_repository,
        )

        with pytest.raises(AIEngineUnavailableError):
            await service.analyze_content("ERROR: test")

    @pytest.mark.asyncio
    async def test_ai_engine_timeout_propagada(
        self,
        mock_parser: MagicMock,
        mock_analyzer: MagicMock,
        mock_repository: AsyncMock,
    ) -> None:
        """AIEngineTimeoutError é propagada sem wrapping."""
        engine = MagicMock()
        engine.diagnose.side_effect = AIEngineTimeoutError("Timeout após 3 tentativas")

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=mock_analyzer,
            ai_engine=engine,
            repository=mock_repository,
        )

        with pytest.raises(AIEngineTimeoutError):
            await service.analyze_content("ERROR: test")

    @pytest.mark.asyncio
    async def test_storage_error_quando_repository_falha(
        self,
        mock_parser: MagicMock,
        mock_analyzer: MagicMock,
        mock_ai_engine: MagicMock,
    ) -> None:
        """Lança StorageError quando repository falha ao persistir."""
        repo = AsyncMock()
        repo.create.side_effect = StorageError("DB write failed")

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=mock_analyzer,
            ai_engine=mock_ai_engine,
            repository=repo,
        )

        with pytest.raises(StorageError):
            await service.analyze_content("ERROR: test")

    @pytest.mark.asyncio
    async def test_storage_error_quando_get_by_id_retorna_none(
        self,
        mock_parser: MagicMock,
        mock_analyzer: MagicMock,
        mock_ai_engine: MagicMock,
    ) -> None:
        """Lança StorageError quando registro recém-criado não é encontrado."""
        repo = AsyncMock()
        repo.create.return_value = "uuid-123"
        repo.get_by_id.return_value = None  # Registro não encontrado

        service = LogAnalysisService(
            parser=mock_parser,
            analyzer=mock_analyzer,
            ai_engine=mock_ai_engine,
            repository=repo,
        )

        with pytest.raises(StorageError) as exc_info:
            await service.analyze_content("ERROR: test")

        assert "uuid-123" in str(exc_info.value)
