"""Testes para GET /api/v1/logs/{id}.

Valida consulta de log por UUID, retorno 404 para IDs inexistentes,
e estrutura da resposta JSON.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

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
    return AsyncMock()


@pytest.fixture
def sample_response() -> LogAnalysisResponse:
    """Cria uma resposta de exemplo para testes."""
    return LogAnalysisResponse(
        id="abc-123-def-456",
        analysis=AnalysisResult(total_entries=10, error_count=3, warning_count=2),
        diagnosis=AIDiagnosis(
            summary="Erro de conexão com banco de dados",
            probable_cause="Pool de conexões esgotado",
            hypotheses=[
                Hypothesis(
                    description="Pool de conexões esgotado",
                    probability="alta",
                    action="Aumentar max_connections",
                ),
                Hypothesis(
                    description="Timeout de rede",
                    probability="média",
                    action="Verificar latência de rede",
                ),
                Hypothesis(
                    description="Deadlock no banco",
                    probability="baixa",
                    action="Analisar queries concorrentes",
                ),
            ],
            suggested_fix="Aumentar pool de conexões para 50",
            confidence=0.85,
        ),
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        total_entries=10,
        summary="Erro de conexão com banco de dados",
    )


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router)
    override_repository(mock_repository)
    return TestClient(app)


class TestGetLogById:
    """Testes para o endpoint GET /api/v1/logs/{id}."""

    def test_returns_200_when_log_exists(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Retorna 200 com dados completos quando log existe."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get("/api/v1/logs/abc-123-def-456")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "abc-123-def-456"
        assert data["summary"] == "Erro de conexão com banco de dados"

    def test_returns_404_when_log_not_found(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 404 quando log não existe."""
        mock_repository.get_by_id.return_value = None

        response = client.get("/api/v1/logs/inexistente-id")

        assert response.status_code == 404
        data = response.json()
        assert "não encontrado" in data["detail"]

    def test_response_contains_analysis(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Resposta contém dados de análise."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get("/api/v1/logs/abc-123-def-456")

        data = response.json()
        assert "analysis" in data
        assert data["analysis"]["total_entries"] == 10
        assert data["analysis"]["error_count"] == 3

    def test_response_contains_diagnosis(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Resposta contém dados de diagnóstico IA."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get("/api/v1/logs/abc-123-def-456")

        data = response.json()
        assert "diagnosis" in data
        assert data["diagnosis"]["probable_cause"] == "Pool de conexões esgotado"
        assert len(data["diagnosis"]["hypotheses"]) == 3

    def test_response_contains_created_at(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Resposta contém timestamp de criação."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get("/api/v1/logs/abc-123-def-456")

        data = response.json()
        assert "created_at" in data
        assert "2024-01-15" in data["created_at"]

    def test_repository_called_with_correct_id(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Repositório é chamado com o ID correto."""
        mock_repository.get_by_id.return_value = sample_response

        client.get("/api/v1/logs/meu-uuid-especifico")

        mock_repository.get_by_id.assert_called_once_with("meu-uuid-especifico")
