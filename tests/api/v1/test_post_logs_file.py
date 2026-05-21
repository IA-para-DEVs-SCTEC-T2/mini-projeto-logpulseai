"""Testes para POST /api/v1/logs/file.

Valida upload de arquivo de log, validações de extensão e conteúdo,
e integração com pipeline de análise via dependency override.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.core.dependencies import get_ai_engine, get_analyzer, get_parser, get_repository
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
    LogEntry,
    LogTemplate,
    SeverityLevel,
)


def _make_response(log_id: str = "new-uuid-123") -> LogAnalysisResponse:
    """Cria LogAnalysisResponse de teste."""
    return LogAnalysisResponse(
        id=log_id,
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


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock do repositório."""
    repo = AsyncMock()
    repo.create.return_value = "new-uuid-123"
    repo.get_by_id.return_value = _make_response()
    return repo


@pytest.fixture
def mock_parser() -> MagicMock:
    """Mock do parser."""
    parser = MagicMock()
    parser.parse.return_value = [
        LogEntry(raw_content="ERROR: test", severity=SeverityLevel.ERROR, message="test")
    ]
    parser.get_templates.return_value = []
    return parser


@pytest.fixture
def mock_analyzer() -> MagicMock:
    """Mock do analyzer."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = AnalysisResult(total_entries=5, error_count=2, warning_count=1)
    return analyzer


@pytest.fixture
def mock_ai_engine() -> MagicMock:
    """Mock do AI engine."""
    engine = MagicMock()
    engine.diagnose.return_value = AIDiagnosis(
        summary="Erro de conexão detectado",
        probable_cause="Timeout de rede",
        hypotheses=[
            Hypothesis(description="Timeout", probability="alta", action="Verificar rede"),
            Hypothesis(description="DNS", probability="média", action="Verificar DNS"),
            Hypothesis(description="Firewall", probability="baixa", action="Verificar regras"),
        ],
        suggested_fix="Aumentar timeout",
        confidence=0.8,
    )
    return engine


@pytest.fixture
def client(
    mock_repository: AsyncMock,
    mock_parser: MagicMock,
    mock_analyzer: MagicMock,
    mock_ai_engine: MagicMock,
) -> TestClient:
    """TestClient com todas as dependências mockadas via DI override."""

    async def override_repo():
        yield mock_repository

    app.dependency_overrides[get_repository] = override_repo
    app.dependency_overrides[get_parser] = lambda: mock_parser
    app.dependency_overrides[get_analyzer] = lambda: mock_analyzer
    app.dependency_overrides[get_ai_engine] = lambda: mock_ai_engine
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestPostLogsFile:
    """Testes para o endpoint POST /api/v1/logs/file."""

    def test_returns_201_with_valid_log_file(self, client: TestClient) -> None:
        """Retorna 201 com arquivo .log válido."""
        content = "2024-01-15 10:00:00 ERROR Connection timeout\n" * 3
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 201
        assert "id" in response.json()

    def test_returns_201_with_valid_txt_file(self, client: TestClient) -> None:
        """Retorna 201 com arquivo .txt válido."""
        content = "ERROR: something went wrong\nWARNING: disk space low\n"
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("errors.txt", file, "text/plain")},
        )

        assert response.status_code == 201

    def test_returns_400_with_invalid_extension(self, client: TestClient) -> None:
        """Retorna 400 para extensão não permitida."""
        file = io.BytesIO(b"some content")

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("data.csv", file, "text/plain")},
        )

        assert response.status_code == 400
        assert "Apenas arquivos" in response.json()["detail"]

    def test_returns_422_with_empty_file(self, client: TestClient) -> None:
        """Retorna 422 para arquivo vazio."""
        file = io.BytesIO(b"")

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 422
        assert "vazio" in response.json()["detail"].lower()

    def test_returns_422_with_whitespace_only_file(self, client: TestClient) -> None:
        """Retorna 422 para arquivo com apenas espaços."""
        file = io.BytesIO(b"   \n\n   \t  ")

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 422
        assert "vazio" in response.json()["detail"].lower()

    def test_returns_503_when_ai_unavailable(
        self, mock_ai_engine: MagicMock, client: TestClient
    ) -> None:
        """Retorna 503 quando motor de IA está indisponível."""
        from src.exceptions import AIEngineUnavailableError

        mock_ai_engine.diagnose.side_effect = AIEngineUnavailableError("Ollama offline")

        content = "ERROR: test error\n" * 3
        file = io.BytesIO(content.encode("utf-8"))

        response = client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        assert response.status_code == 503

    def test_repository_create_called(
        self, mock_repository: AsyncMock, client: TestClient
    ) -> None:
        """Repositório create é chamado após processamento."""
        content = "INFO: application started\nERROR: connection failed\n"
        file = io.BytesIO(content.encode("utf-8"))

        client.post(
            "/api/v1/logs/file",
            files={"file": ("app.log", file, "text/plain")},
        )

        mock_repository.create.assert_called_once()
