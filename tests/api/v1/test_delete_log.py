"""Testes para DELETE /api/v1/logs/{id}.

Valida remoção de log por UUID, retorno 204 para sucesso,
retorno 404 para IDs inexistentes, e retorno 422 para UUIDs inválidos.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.logs import router
from src.core.dependencies import get_repository

# UUID válido para testes
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"
ANOTHER_VALID_UUID = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Cria um mock do repositório para testes."""
    return AsyncMock()


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/logs")
    
    # Override da dependência do repositório
    app.dependency_overrides[get_repository] = lambda: mock_repository
    
    return TestClient(app)


class TestDeleteLog:
    """Testes para o endpoint DELETE /api/v1/logs/{id}."""

    def test_returns_204_when_log_deleted(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 204 quando log é removido com sucesso."""
        mock_repository.delete.return_value = True

        response = client.delete(f"/api/v1/logs/{VALID_UUID}")

        assert response.status_code == 204
        assert response.content == b""

    def test_returns_404_when_log_not_found(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 404 quando log não existe."""
        mock_repository.delete.return_value = False

        response = client.delete(f"/api/v1/logs/{ANOTHER_VALID_UUID}")

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
            response = client.delete(f"/api/v1/logs/{invalid_uuid}")
            assert response.status_code == 422, f"Failed for: {invalid_uuid}"
            data = response.json()
            assert "detail" in data

    def test_repository_called_with_correct_id(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Repositório delete é chamado com o ID correto (como string)."""
        mock_repository.delete.return_value = True

        client.delete(f"/api/v1/logs/{ANOTHER_VALID_UUID}")

        mock_repository.delete.assert_called_once_with(ANOTHER_VALID_UUID)
