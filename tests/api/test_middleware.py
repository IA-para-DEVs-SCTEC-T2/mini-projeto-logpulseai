"""Testes para o middleware de tratamento de erros do LogPulse IA.

Valida que cada tipo de exceção do domínio é mapeado para o HTTP status
code correto e que todas as respostas de erro contêm o campo `detail`.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware import register_exception_handlers
from src.exceptions import (
    AIEngineError,
    AIEngineTimeoutError,
    AIEngineUnavailableError,
    AnalysisError,
    ConfigError,
    LogPulseError,
    NotFoundError,
    ParsingError,
    StorageError,
    ValidationError,
)


def _make_app_raising(exc: Exception) -> FastAPI:
    """Cria uma aplicação FastAPI mínima que lança a exceção fornecida.

    Args:
        exc: Exceção a ser lançada pelo endpoint de teste.

    Returns:
        Aplicação FastAPI com handler de exceções registrado.
    """
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    async def _raise() -> None:
        raise exc

    return app


class TestParsingErrorMapping:
    """ParsingError deve retornar HTTP 422."""

    def test_status_code(self) -> None:
        """ParsingError → HTTP 422 Unprocessable Entity."""
        client = TestClient(_make_app_raising(ParsingError("formato inválido")))
        response = client.get("/test")
        assert response.status_code == 422

    def test_detail_field_present(self) -> None:
        """Resposta de ParsingError contém campo detail."""
        client = TestClient(_make_app_raising(ParsingError("formato inválido")))
        response = client.get("/test")
        assert "detail" in response.json()

    def test_detail_contains_message(self) -> None:
        """Campo detail reflete a mensagem da exceção."""
        client = TestClient(_make_app_raising(ParsingError("formato inválido")))
        response = client.get("/test")
        assert "formato inválido" in response.json()["detail"]


class TestValidationErrorMapping:
    """ValidationError deve retornar HTTP 422."""

    def test_status_code(self) -> None:
        """ValidationError → HTTP 422 Unprocessable Entity."""
        client = TestClient(_make_app_raising(ValidationError("extensão não suportada")))
        response = client.get("/test")
        assert response.status_code == 422

    def test_detail_field_present(self) -> None:
        """Resposta de ValidationError contém campo detail."""
        client = TestClient(_make_app_raising(ValidationError("extensão não suportada")))
        response = client.get("/test")
        assert "detail" in response.json()


class TestNotFoundErrorMapping:
    """NotFoundError deve retornar HTTP 404."""

    def test_status_code(self) -> None:
        """NotFoundError → HTTP 404 Not Found."""
        client = TestClient(_make_app_raising(NotFoundError("log não encontrado")))
        response = client.get("/test")
        assert response.status_code == 404

    def test_detail_field_present(self) -> None:
        """Resposta de NotFoundError contém campo detail."""
        client = TestClient(_make_app_raising(NotFoundError("log não encontrado")))
        response = client.get("/test")
        assert "detail" in response.json()

    def test_detail_contains_message(self) -> None:
        """Campo detail reflete a mensagem da exceção."""
        client = TestClient(_make_app_raising(NotFoundError("log não encontrado")))
        response = client.get("/test")
        assert "log não encontrado" in response.json()["detail"]


class TestAIEngineUnavailableMapping:
    """AIEngineUnavailableError deve retornar HTTP 503."""

    def test_status_code(self) -> None:
        """AIEngineUnavailableError → HTTP 503 Service Unavailable."""
        client = TestClient(_make_app_raising(AIEngineUnavailableError("Ollama offline")))
        response = client.get("/test")
        assert response.status_code == 503

    def test_detail_field_present(self) -> None:
        """Resposta de AIEngineUnavailableError contém campo detail."""
        client = TestClient(_make_app_raising(AIEngineUnavailableError("Ollama offline")))
        response = client.get("/test")
        assert "detail" in response.json()

    def test_detail_contains_message(self) -> None:
        """Campo detail reflete a mensagem da exceção."""
        client = TestClient(_make_app_raising(AIEngineUnavailableError("Ollama offline")))
        response = client.get("/test")
        assert "Ollama offline" in response.json()["detail"]


class TestAIEngineTimeoutMapping:
    """AIEngineTimeoutError deve retornar HTTP 504."""

    def test_status_code(self) -> None:
        """AIEngineTimeoutError → HTTP 504 Gateway Timeout."""
        client = TestClient(_make_app_raising(AIEngineTimeoutError("timeout após 30s")))
        response = client.get("/test")
        assert response.status_code == 504

    def test_detail_field_present(self) -> None:
        """Resposta de AIEngineTimeoutError contém campo detail."""
        client = TestClient(_make_app_raising(AIEngineTimeoutError("timeout após 30s")))
        response = client.get("/test")
        assert "detail" in response.json()

    def test_detail_contains_message(self) -> None:
        """Campo detail reflete a mensagem da exceção."""
        client = TestClient(_make_app_raising(AIEngineTimeoutError("timeout após 30s")))
        response = client.get("/test")
        assert "timeout após 30s" in response.json()["detail"]


class TestAIEngineErrorMapping:
    """AIEngineError genérico deve retornar HTTP 502."""

    def test_status_code(self) -> None:
        """AIEngineError → HTTP 502 Bad Gateway."""
        client = TestClient(_make_app_raising(AIEngineError("erro genérico de IA")))
        response = client.get("/test")
        assert response.status_code == 502

    def test_detail_field_present(self) -> None:
        """Resposta de AIEngineError contém campo detail."""
        client = TestClient(_make_app_raising(AIEngineError("erro genérico de IA")))
        response = client.get("/test")
        assert "detail" in response.json()


class TestStorageErrorMapping:
    """StorageError deve retornar HTTP 500."""

    def test_status_code(self) -> None:
        """StorageError → HTTP 500 Internal Server Error."""
        client = TestClient(_make_app_raising(StorageError("falha no SQLite")))
        response = client.get("/test")
        assert response.status_code == 500

    def test_detail_field_present(self) -> None:
        """Resposta de StorageError contém campo detail."""
        client = TestClient(_make_app_raising(StorageError("falha no SQLite")))
        response = client.get("/test")
        assert "detail" in response.json()

    def test_detail_does_not_expose_internal_message(self) -> None:
        """StorageError não expõe mensagem interna (segurança)."""
        client = TestClient(_make_app_raising(StorageError("senha do banco: abc123")))
        response = client.get("/test")
        # Mensagem interna não deve vazar para o cliente
        assert "abc123" not in response.json()["detail"]


class TestAnalysisErrorMapping:
    """AnalysisError deve retornar HTTP 500."""

    def test_status_code(self) -> None:
        """AnalysisError → HTTP 500 Internal Server Error."""
        client = TestClient(_make_app_raising(AnalysisError("estado inconsistente")))
        response = client.get("/test")
        assert response.status_code == 500

    def test_detail_field_present(self) -> None:
        """Resposta de AnalysisError contém campo detail."""
        client = TestClient(_make_app_raising(AnalysisError("estado inconsistente")))
        response = client.get("/test")
        assert "detail" in response.json()


class TestConfigErrorMapping:
    """ConfigError deve retornar HTTP 500."""

    def test_status_code(self) -> None:
        """ConfigError → HTTP 500 Internal Server Error."""
        client = TestClient(_make_app_raising(ConfigError("toml inválido")))
        response = client.get("/test")
        assert response.status_code == 500

    def test_detail_field_present(self) -> None:
        """Resposta de ConfigError contém campo detail."""
        client = TestClient(_make_app_raising(ConfigError("toml inválido")))
        response = client.get("/test")
        assert "detail" in response.json()


class TestLogPulseErrorFallback:
    """LogPulseError base deve retornar HTTP 500 como fallback."""

    def test_status_code(self) -> None:
        """LogPulseError genérica → HTTP 500 Internal Server Error."""
        client = TestClient(_make_app_raising(LogPulseError("erro desconhecido")))
        response = client.get("/test")
        assert response.status_code == 500

    def test_detail_field_present(self) -> None:
        """Resposta de LogPulseError contém campo detail."""
        client = TestClient(_make_app_raising(LogPulseError("erro desconhecido")))
        response = client.get("/test")
        assert "detail" in response.json()


class TestAllErrorsHaveDetailField:
    """Todos os tipos de exceção devem retornar campo detail na resposta."""

    @pytest.mark.parametrize(
        "exc",
        [
            ParsingError("parsing"),
            ValidationError("validation"),
            NotFoundError("not found"),
            AIEngineUnavailableError("unavailable"),
            AIEngineTimeoutError("timeout"),
            AIEngineError("ai error"),
            StorageError("storage"),
            AnalysisError("analysis"),
            ConfigError("config"),
            LogPulseError("base"),
        ],
    )
    def test_detail_field_always_present(self, exc: Exception) -> None:
        """Campo detail está presente em todas as respostas de erro."""
        client = TestClient(_make_app_raising(exc))
        response = client.get("/test")
        body = response.json()
        assert "detail" in body, f"Campo 'detail' ausente para {type(exc).__name__}"
        assert body["detail"]  # não deve ser vazio ou None
