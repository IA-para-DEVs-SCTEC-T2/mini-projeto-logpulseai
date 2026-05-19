"""Testes para POST /api/v1/logs/file.

Valida upload de arquivo de log, validações de extensão e tamanho,
e integração com pipeline de análise.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import override_repository
from src.api.v1.logs_file import router
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
    repo.create.return_value = "new-uuid-123"
    repo.get_by_id.return_value = LogAnalysisResponse(
        id="new-uuid-123",
        analysis=AnalysisResult(total_entries=5, error_count=2, warning_count=1),
        diagnosis=AIDiagnosis(
            summary="Erro de conexão detectado",
            probable_cause="Timeout de rede",
            hypotheses=[
                Hypothesis(description="Timeout", probability="alta", action="Verificar rede"),
                Hypothesis(description="DNS", probability="média", action="Verificar DNS"),
                Hypothesis(description="Firewall", probability="baixa", action="Verificar regras"),
            ],
            suggested_fix="Aumentar timeout",
            confidence=0.8,
        ),
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        total_entries=5,
        summary="Erro de conexão detectado",
    )
    return repo


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router)
    override_repository(mock_repository)
    return TestClient(app)


class TestPostLogsFile:
    """Testes para o endpoint POST /api/v1/logs/file."""

    @patch("src.api.v1.logs_file.OllamaAIEngine")
    def test_returns_201_with_valid_log_file(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 201 com arquivo .log válido."""
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

        content = "2024-01-15 10:00:00 ERROR Connection timeout\n" * 5
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 201

    @patch("src.api.v1.logs_file.OllamaAIEngine")
    def test_returns_201_with_valid_txt_file(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 201 com arquivo .txt válido."""
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

        content = "ERROR: something went wrong\nWARNING: disk space low\n"
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("errors.txt", file, "text/plain")},
        )

        assert response.status_code == 201

    def test_returns_400_with_invalid_extension(
        self,
        client: TestClient,
    ) -> None:
        """Retorna 400 para extensão não permitida."""
        content = "some content"
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("data.csv", file, "text/plain")},
        )

        assert response.status_code == 400
        assert "Apenas arquivos" in response.json()["detail"]

    def test_returns_400_with_empty_file(
        self,
        client: TestClient,
    ) -> None:
        """Retorna 400 para arquivo vazio."""
        file = io.BytesIO(b"")

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 400
        assert "vazio" in response.json()["detail"]

    def test_returns_400_with_whitespace_only_file(
        self,
        client: TestClient,
    ) -> None:
        """Retorna 400 para arquivo com apenas espaços."""
        file = io.BytesIO(b"   \n\n   \t  ")

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 400
        assert "vazio" in response.json()["detail"]

    @patch("src.api.v1.logs_file.OllamaAIEngine")
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

        content = "ERROR: test error\n" * 3
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 503
        assert "indisponível" in response.json()["detail"]

    @patch("src.api.v1.logs_file.OllamaAIEngine")
    def test_repository_create_called(
        self,
        mock_engine_class: AsyncMock,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Repositório create é chamado após processamento."""
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

        content = "INFO: application started\nERROR: connection failed\n"
        file = io.BytesIO(content.encode("utf-8"))

        client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        mock_repository.create.assert_called_once()
