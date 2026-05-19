"""Testes para GET /api/v1/logs.

Valida listagem paginada de logs, parâmetros de paginação,
e estrutura da resposta JSON.
"""

from __future__ import annotations

from datetime import UTC, datetime
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


def _make_log_response(log_id: str) -> LogAnalysisResponse:
    """Cria uma resposta de log para testes."""
    return LogAnalysisResponse(
        id=log_id,
        analysis=AnalysisResult(total_entries=5, error_count=1, warning_count=1),
        diagnosis=AIDiagnosis(
            summary=f"Resumo do log {log_id}",
            probable_cause="Causa teste",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="A1"),
                Hypothesis(description="H2", probability="média", action="A2"),
                Hypothesis(description="H3", probability="baixa", action="A3"),
            ],
            suggested_fix="Fix teste",
            confidence=0.7,
        ),
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        total_entries=5,
        summary=f"Resumo do log {log_id}",
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Cria um mock do repositório para testes."""
    repo = AsyncMock()
    repo.count.return_value = 50
    repo.list_paginated.return_value = [
        _make_log_response(f"id-{i}") for i in range(20)
    ]
    return repo


@pytest.fixture
def client(mock_repository: AsyncMock) -> TestClient:
    """Cria um TestClient com o repositório mockado."""
    app = FastAPI()
    app.include_router(router)
    override_repository(mock_repository)
    return TestClient(app)


class TestGetLogsList:
    """Testes para o endpoint GET /api/v1/logs."""

    def test_returns_200_with_default_pagination(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Retorna 200 com paginação padrão (page=1, page_size=20)."""
        response = client.get("/api/v1/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 50
        assert data["pages"] == 3

    def test_returns_items_list(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Resposta contém lista de itens."""
        response = client.get("/api/v1/logs")

        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 20

    def test_custom_page_and_page_size(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Aceita parâmetros customizados de paginação."""
        mock_repository.list_paginated.return_value = [
            _make_log_response(f"id-{i}") for i in range(10)
        ]

        response = client.get("/api/v1/logs?page=2&page_size=10")

        assert response.status_code == 200
        mock_repository.list_paginated.assert_called_once_with(2, 10)

    def test_page_size_max_100(
        self,
        client: TestClient,
    ) -> None:
        """page_size não pode exceder 100."""
        response = client.get("/api/v1/logs?page_size=101")

        assert response.status_code == 422

    def test_page_min_1(
        self,
        client: TestClient,
    ) -> None:
        """page não pode ser menor que 1."""
        response = client.get("/api/v1/logs?page=0")

        assert response.status_code == 422

    def test_empty_list_returns_zero_pages(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Lista vazia retorna pages=0."""
        mock_repository.count.return_value = 0
        mock_repository.list_paginated.return_value = []

        response = client.get("/api/v1/logs")

        data = response.json()
        assert data["total"] == 0
        assert data["pages"] == 0
        assert data["items"] == []

    def test_pages_calculation_rounds_up(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Cálculo de páginas arredonda para cima."""
        mock_repository.count.return_value = 21
        mock_repository.list_paginated.return_value = [
            _make_log_response("id-1")
        ]

        response = client.get("/api/v1/logs?page_size=10")

        data = response.json()
        assert data["pages"] == 3  # ceil(21/10) = 3

    def test_response_structure(
        self,
        client: TestClient,
        mock_repository: AsyncMock,
    ) -> None:
        """Resposta tem estrutura completa com todos os campos."""
        response = client.get("/api/v1/logs")

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
