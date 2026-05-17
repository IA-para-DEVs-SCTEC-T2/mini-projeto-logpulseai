"""Testes para a hierarquia de exceções customizadas do LogPulse IA.

Valida a estrutura hierárquica, herança, instanciação e mensagens
de todas as exceções do domínio.
"""

from __future__ import annotations

import pytest

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


class TestHierarchy:
    """Testes de hierarquia e herança das exceções."""

    def test_logpulse_error_is_base_exception(self) -> None:
        """LogPulseError herda de Exception."""
        assert issubclass(LogPulseError, Exception)

    def test_config_error_inherits_from_base(self) -> None:
        """ConfigError herda de LogPulseError."""
        assert issubclass(ConfigError, LogPulseError)

    def test_validation_error_inherits_from_base(self) -> None:
        """ValidationError herda de LogPulseError."""
        assert issubclass(ValidationError, LogPulseError)

    def test_not_found_error_inherits_from_base(self) -> None:
        """NotFoundError herda de LogPulseError."""
        assert issubclass(NotFoundError, LogPulseError)

    def test_ai_engine_error_inherits_from_base(self) -> None:
        """AIEngineError herda de LogPulseError."""
        assert issubclass(AIEngineError, LogPulseError)

    def test_ai_engine_timeout_inherits_from_ai_engine(self) -> None:
        """AIEngineTimeoutError herda de AIEngineError."""
        assert issubclass(AIEngineTimeoutError, AIEngineError)

    def test_ai_engine_unavailable_inherits_from_ai_engine(self) -> None:
        """AIEngineUnavailableError herda de AIEngineError."""
        assert issubclass(AIEngineUnavailableError, AIEngineError)

    def test_parsing_error_inherits_from_base(self) -> None:
        """ParsingError herda de LogPulseError."""
        assert issubclass(ParsingError, LogPulseError)

    def test_analysis_error_inherits_from_base(self) -> None:
        """AnalysisError herda de LogPulseError."""
        assert issubclass(AnalysisError, LogPulseError)

    def test_storage_error_inherits_from_base(self) -> None:
        """StorageError herda de LogPulseError."""
        assert issubclass(StorageError, LogPulseError)


class TestInstantiation:
    """Testes de instanciação e mensagens de erro."""

    def test_logpulse_error_with_message(self) -> None:
        """LogPulseError pode ser instanciada com mensagem."""
        exc = LogPulseError("erro genérico")
        assert str(exc) == "erro genérico"

    def test_config_error_with_message(self) -> None:
        """ConfigError pode ser instanciada com mensagem descritiva."""
        exc = ConfigError("logpulse.toml não encontrado")
        assert "logpulse.toml" in str(exc)

    def test_validation_error_with_message(self) -> None:
        """ValidationError pode ser instanciada com mensagem descritiva."""
        exc = ValidationError("Extensão .csv não é aceita")
        assert ".csv" in str(exc)

    def test_not_found_error_with_message(self) -> None:
        """NotFoundError pode ser instanciada com mensagem descritiva."""
        exc = NotFoundError("Log com ID 'abc-123' não encontrado")
        assert "abc-123" in str(exc)

    def test_ai_engine_timeout_with_message(self) -> None:
        """AIEngineTimeoutError pode ser instanciada com mensagem."""
        exc = AIEngineTimeoutError("Timeout após 3 tentativas (30s)")
        assert "30s" in str(exc)

    def test_ai_engine_unavailable_with_message(self) -> None:
        """AIEngineUnavailableError pode ser instanciada com mensagem."""
        exc = AIEngineUnavailableError("Ollama não está em execução na porta 11434")
        assert "11434" in str(exc)

    def test_parsing_error_with_message(self) -> None:
        """ParsingError pode ser instanciada com mensagem."""
        exc = ParsingError("Formato de log não reconhecido")
        assert "não reconhecido" in str(exc)

    def test_analysis_error_with_message(self) -> None:
        """AnalysisError pode ser instanciada com mensagem."""
        exc = AnalysisError("Estado inconsistente no LogStream")
        assert "inconsistente" in str(exc)

    def test_storage_error_with_message(self) -> None:
        """StorageError pode ser instanciada com mensagem."""
        exc = StorageError("Falha ao conectar ao SQLite")
        assert "SQLite" in str(exc)


class TestCatchBehavior:
    """Testes de captura hierárquica (catch behavior)."""

    def test_catch_all_with_logpulse_error(self) -> None:
        """Todas as exceções do domínio podem ser capturadas com LogPulseError."""
        exceptions = [
            ConfigError("test"),
            ValidationError("test"),
            NotFoundError("test"),
            AIEngineError("test"),
            AIEngineTimeoutError("test"),
            AIEngineUnavailableError("test"),
            ParsingError("test"),
            AnalysisError("test"),
            StorageError("test"),
        ]
        for exc in exceptions:
            with pytest.raises(LogPulseError):
                raise exc

    def test_catch_ai_subtypes_with_ai_engine_error(self) -> None:
        """AIEngineTimeoutError e AIEngineUnavailableError capturadas com AIEngineError."""
        with pytest.raises(AIEngineError):
            raise AIEngineTimeoutError("timeout")

        with pytest.raises(AIEngineError):
            raise AIEngineUnavailableError("unavailable")

    def test_storage_error_not_caught_by_ai_engine_error(self) -> None:
        """StorageError NÃO é capturada por AIEngineError."""
        with pytest.raises(StorageError):
            raise StorageError("db error")

        # Confirma que não é subclasse de AIEngineError
        assert not issubclass(StorageError, AIEngineError)

    def test_parsing_error_not_caught_by_storage_error(self) -> None:
        """ParsingError NÃO é capturada por StorageError."""
        assert not issubclass(ParsingError, StorageError)
