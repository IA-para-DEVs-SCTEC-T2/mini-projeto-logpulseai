"""Testes para POST /api/v1/logs/text.

Valida envio de log via texto, validações de conteúdo,
e integração com pipeline de análise.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import override_repository
from src.api.v1.logs import router
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
)


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Cria um mock do repositório para testes."""
    repo = AsyncMock()
    repo.create.return_value = "new-uuid-456"
    repo.get_by_id.return_value = LogAnalysisResponse(
        id="new-uuid-456",
        analysis=AnalysisResult(total_entries=3, error_count=1, warning_count=1),
        diagnosis=AIDiagnosis(
            summary="Erro detectado no log",
            probable_cause="Falha de conexão",
            hypotheses=[
                Hypothesis(description="Timeout", probability="alta", action="Verificar rede"),
                Hypothesis(description="DNS", probability="média", action="Verificar DNS"),
                Hypothesis(description="Firewall", probability="baixa", action="Verificar regras"),
            ],
            suggested_fix="Aumentar timeout",
            confidence=0.75,
        ),
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        total_entries=3,
        summary="Erro detectado no log",
    )
    return repo


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router)
    override_repository(mock_repository)
    return TestClient(app)


class TestPostLogsText:
    """Testes para o endpoint POST /api/v1/logs/text."""

    @patch("src.api.v1.logs_text.OllamaAIEngine")
    def test_returns_201_with_valid_text(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 201 com texto de log válido."""
        mock_engine = mock_engine_class.return_value
        mock_engine.diagnose.return_value = AIDiagnosis(
            summary="Teste",
            probable_cause="Causa",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="A1"),
                Hypothesis(description="H2", probability="média", action="A2"),
                Hypothesis(description="H3", probability="baixa", action="A3"),
            ],
            suggested_fix="Fix",
            confidence=0.9,
        )

        response = client.post(
            "/api/v1/logs/text",
            json={"content": "2024-01-15 ERROR Connection timeout\nWARNING disk low"},
        )

        assert response.status_code == 201

    @patch("src.api.v1.logs_text.OllamaAIEngine")
    def test_response_contains_id(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Resposta contém ID do registro criado."""
        mock_engine = mock_engine_class.return_value
        mock_engine.diagnose.return_value = AIDiagnosis(
            summary="Teste",
            probable_cause="Causa",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="A1"),
                Hypothesis(description="H2", probability="média", action="A2"),
                Hypothesis(description="H3", probability="baixa", action="A3"),
            ],
            suggested_fix="Fix",
            confidence=0.9,
        )

        response = client.post(
            "/api/v1/logs/text",
            json={"content": "ERROR: something failed"},
        )

        data = response.json()
        assert "id" in data
        assert data["id"] == "new-uuid-456"

    def test_returns_422_with_empty_content(
        self,
        client: TestClient,
    ) -> None:
        """Retorna 422 para conteúdo vazio (validação Pydantic min_length=1)."""
        response = client.post(
            "/api/v1/logs/text",
            json={"content": ""},
        )

        assert response.status_code == 422

    def test_returns_422_without_content_field(
        self,
        client: TestClient,
    ) -> None:
        """Retorna 422 quando campo content está ausente."""
        response = client.post(
            "/api/v1/logs/text",
            json={},
        )

        assert response.status_code == 422

    def test_returns_400_with_whitespace_only(
        self,
        client: TestClient,
    ) -> None:
        """Retorna 400 para conteúdo com apenas espaços."""
        response = client.post(
            "/api/v1/logs/text",
            json={"content": "   \n\n   "},
        )

        assert response.status_code == 400
        assert "vazio" in response.json()["detail"]

    @patch("src.api.v1.logs_text.OllamaAIEngine")
    def test_returns_503_when_ai_unavailable(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 503 quando motor de IA está indisponível."""
        from src.exceptions import AIEngineUnavailableError

        mock_engine = mock_engine_class.return_value
        mock_engine.diagnose.side_effect = AIEngineUnavailableError("Ollama offline")

        response = client.post(
            "/api/v1/logs/text",
            json={"content": "ERROR: test error\nWARNING: disk low"},
        )

        assert response.status_code == 503
        assert "indisponível" in response.json()["detail"]

    @patch("src.api.v1.logs_text.OllamaAIEngine")
    def test_returns_503_when_ai_timeout(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 503 quando motor de IA não responde (timeout)."""
        from src.exceptions import AIEngineTimeoutError

        mock_engine = mock_engine_class.return_value
        mock_engine.diagnose.side_effect = AIEngineTimeoutError("Timeout após 3 tentativas")

        response = client.post(
            "/api/v1/logs/text",
            json={"content": "ERROR: test error\nWARNING: disk low"},
        )

        assert response.status_code == 503
        assert "não respondeu" in response.json()["detail"]

    @patch("src.api.v1.logs_text.OllamaAIEngine")
    def test_repository_create_called_with_content(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Repositório create é chamado com o conteúdo correto."""
        mock_engine = mock_engine_class.return_value
        mock_engine.diagnose.return_value = AIDiagnosis(
            summary="Teste",
            probable_cause="Causa",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="A1"),
                Hypothesis(description="H2", probability="média", action="A2"),
                Hypothesis(description="H3", probability="baixa", action="A3"),
            ],
            suggested_fix="Fix",
            confidence=0.9,
        )

        content = "INFO: app started\nERROR: connection failed"
        client.post(
            "/api/v1/logs/text",
            json={"content": content},
        )

        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args
        assert call_args[0][0] == content
