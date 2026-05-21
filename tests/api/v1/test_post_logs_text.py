"""Testes para POST /api/v1/logs/text.

Valida envio de log via texto, validações de conteúdo,
e integração com pipeline de análise via dependency override.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.core.dependencies import get_ai_engine, get_analyzer, get_parser, get_repository
from src.exceptions import AIEngineTimeoutError, AIEngineUnavailableError
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
    LogEntry,
    SeverityLevel,
)


def _make_response(log_id: str = "new-uuid-456") -> LogAnalysisResponse:
    """Cria LogAnalysisResponse de teste."""
    return LogAnalysisResponse(
        id=log_id,
        analyzed_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        metrics={"total_logs": 3, "errors": 1, "criticals": 0},
        confidence=0.75,
    )


def _make_diagnosis() -> AIDiagnosis:
    return AIDiagnosis(
        summary="Erro detectado no log",
        probable_cause="Falha de conexão",
        hypotheses=[
            Hypothesis(description="Timeout", probability="alta", action="Verificar rede"),
            Hypothesis(description="DNS", probability="média", action="Verificar DNS"),
            Hypothesis(description="Firewall", probability="baixa", action="Verificar regras"),
        ],
        suggested_fix="Aumentar timeout",
        confidence=0.75,
    )


class TestPostLogsText:
    """Testes para o endpoint POST /api/v1/logs/text."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Configura mocks compartilhados para todos os testes da classe."""
        self.mock_repo = AsyncMock()
        self.mock_repo.create.return_value = "new-uuid-456"
        self.mock_repo.get_by_id.return_value = _make_response()

        self.mock_parser = MagicMock()
        self.mock_parser.parse.return_value = [
            LogEntry(raw_content="ERROR: test", severity=SeverityLevel.ERROR, message="test")
        ]
        self.mock_parser.get_templates.return_value = []

        self.mock_analyzer = MagicMock()
        self.mock_analyzer.analyze.return_value = AnalysisResult(
            total_entries=3, error_count=1, warning_count=1
        )

        self.mock_ai_engine = MagicMock()
        self.mock_ai_engine.diagnose.return_value = _make_diagnosis()

        async def override_repo():
            yield self.mock_repo

        app.dependency_overrides[get_repository] = override_repo
        app.dependency_overrides[get_parser] = lambda: self.mock_parser
        app.dependency_overrides[get_analyzer] = lambda: self.mock_analyzer
        app.dependency_overrides[get_ai_engine] = lambda: self.mock_ai_engine

        self.client = TestClient(app)

        yield

        app.dependency_overrides.clear()

    def test_returns_201_with_valid_text(self) -> None:
        """Retorna 201 com texto de log válido."""
        response = self.client.post(
            "/api/v1/logs/text",
            json={"content": "2024-01-15 ERROR Connection timeout\nWARNING disk low"},
        )
        assert response.status_code == 201

    def test_response_contains_id(self) -> None:
        """Resposta contém ID do registro criado."""
        response = self.client.post(
            "/api/v1/logs/text",
            json={"content": "ERROR: something failed"},
        )
        data = response.json()
        assert "id" in data
        assert data["id"] == "new-uuid-456"

    def test_returns_422_with_empty_content(self) -> None:
        """Retorna 422 para conteúdo vazio (validação Pydantic min_length=1)."""
        response = self.client.post(
            "/api/v1/logs/text",
            json={"content": ""},
        )
        assert response.status_code == 422

    def test_returns_422_without_content_field(self) -> None:
        """Retorna 422 quando campo content está ausente."""
        response = self.client.post(
            "/api/v1/logs/text",
            json={},
        )
        assert response.status_code == 422

    def test_returns_503_when_ai_unavailable(self) -> None:
        """Retorna 503 quando motor de IA está indisponível."""
        self.mock_ai_engine.diagnose.side_effect = AIEngineUnavailableError("Ollama offline")

        response = self.client.post(
            "/api/v1/logs/text",
            json={"content": "ERROR: test error\nWARNING: disk low"},
        )
        assert response.status_code == 503

    def test_returns_504_when_ai_timeout(self) -> None:
        """Retorna 504 quando motor de IA não responde (timeout)."""
        self.mock_ai_engine.diagnose.side_effect = AIEngineTimeoutError("Timeout")

        response = self.client.post(
            "/api/v1/logs/text",
            json={"content": "ERROR: test error\nWARNING: disk low"},
        )
        assert response.status_code == 504

    def test_repository_create_called_with_content(self) -> None:
        """Repositório create é chamado com o conteúdo correto."""
        content = "INFO: app started\nERROR: connection failed"

        self.client.post(
            "/api/v1/logs/text",
            json={"content": content},
        )

        self.mock_repo.create.assert_called_once()
        call_args = self.mock_repo.create.call_args
        assert call_args[0][0] == content
