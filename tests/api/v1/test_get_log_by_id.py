"""Testes para GET /api/v1/logs/{id}.

Valida consulta de log por UUID, retorno 404 para IDs inexistentes,
retorno 422 para UUIDs inválidos, e estrutura da resposta JSON.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.logs import router
from src.core.dependencies import get_repository
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
)

# UUID válido para testes
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"
ANOTHER_VALID_UUID = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Cria um mock do repositório para testes."""
    return AsyncMock()


@pytest.fixture
def sample_response() -> LogAnalysisResponse:
    """Cria uma resposta de exemplo para testes."""
    return LogAnalysisResponse(
        id=VALID_UUID,
        analyzed_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        metrics={
            "total_logs": 10,
            "errors": 3,
            "criticals": 0
        },
        issues=[],
        recommended_actions=[
            "Aumentar pool de conexões para 50",
            "Verificar latência de rede",
            "Analisar queries concorrentes"
        ],
        confidence=0.85
    )


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/logs")
    
    # Override the dependency
    async def override_get_repository():
        yield mock_repository
    
    app.dependency_overrides[get_repository] = override_get_repository
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

        response = client.get(f"/api/v1/logs/{VALID_UUID}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == VALID_UUID
        assert data["confidence"] == 0.85

    def test_returns_404_when_log_not_found(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 404 quando log não existe."""
        mock_repository.get_by_id.return_value = None

        response = client.get(f"/api/v1/logs/{ANOTHER_VALID_UUID}")

        assert response.status_code == 404
        data = response.json()
        assert "não encontrado" in data["detail"]

    def test_returns_422_when_uuid_invalid(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 422 quando UUID é inválido."""
        # Testa vários formatos inválidos
        invalid_uuids = [
            "abc-123-def-456",  # formato errado
            "not-a-uuid",       # não é UUID
            "12345",            # muito curto
            "550e8400-e29b-41d4-a716",  # incompleto
        ]
        
        for invalid_uuid in invalid_uuids:
            response = client.get(f"/api/v1/logs/{invalid_uuid}")
            assert response.status_code == 422, f"Failed for: {invalid_uuid}"
            data = response.json()
            assert "detail" in data

    def test_response_contains_analysis(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Resposta contém dados de métricas."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get(f"/api/v1/logs/{VALID_UUID}")

        data = response.json()
        assert "metrics" in data
        assert data["metrics"]["total_logs"] == 10
        assert data["metrics"]["errors"] == 3

    def test_response_contains_diagnosis(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Resposta contém ações recomendadas."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get(f"/api/v1/logs/{VALID_UUID}")

        data = response.json()
        assert "recommended_actions" in data
        assert len(data["recommended_actions"]) == 3
        assert "Aumentar pool de conexões para 50" in data["recommended_actions"]

    def test_response_contains_created_at(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Resposta contém timestamp de análise."""
        mock_repository.get_by_id.return_value = sample_response

        response = client.get(f"/api/v1/logs/{VALID_UUID}")

        data = response.json()
        assert "analyzed_at" in data
        assert "2024-01-15" in data["analyzed_at"]

    def test_repository_called_with_correct_id(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
        sample_response: LogAnalysisResponse,
    ) -> None:
        """Repositório é chamado com o ID correto (como string)."""
        mock_repository.get_by_id.return_value = sample_response

        client.get(f"/api/v1/logs/{ANOTHER_VALID_UUID}")

        mock_repository.get_by_id.assert_called_once_with(ANOTHER_VALID_UUID)
