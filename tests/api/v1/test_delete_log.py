"""Testes para DELETE /api/v1/logs/{id}.

Valida remoção de log por UUID, retorno 204 para sucesso,
e retorno 404 para IDs inexistentes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import override_repository
from src.api.v1.logs import router


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Cria um mock do repositório para testes."""
    return AsyncMock()


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router)
    override_repository(mock_repository)
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

        response = client.delete("/api/v1/logs/abc-123-def-456")

        assert response.status_code == 204
        assert response.content == b""

    def test_returns_404_when_log_not_found(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 404 quando log não existe."""
        mock_repository.delete.return_value = False

        response = client.delete("/api/v1/logs/inexistente-id")

        assert response.status_code == 404
        data = response.json()
        assert "não encontrado" in data["detail"]

    def test_repository_called_with_correct_id(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Repositório delete é chamado com o ID correto."""
        mock_repository.delete.return_value = True

        client.delete("/api/v1/logs/meu-uuid-especifico")

        mock_repository.delete.assert_called_once_with("meu-uuid-especifico")
