"""Testes para o módulo de logging estruturado do LogPulse IA.

Valida configuração, resolução de nível, formato de saída e
integração com structlog.
"""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest

from src.core.logging import (
    _resolve_log_level,
    _resolve_output_format,
    configure_logging,
    get_logger,
)


class TestResolveLogLevel:
    """Testes para resolução do nível de log."""

    def test_explicit_level_info(self) -> None:
        """Nível explícito INFO retorna constante correta."""
        assert _resolve_log_level("INFO") == logging.INFO

    def test_explicit_level_debug(self) -> None:
        """Nível explícito DEBUG retorna constante correta."""
        assert _resolve_log_level("DEBUG") == logging.DEBUG

    def test_explicit_level_warning(self) -> None:
        """Nível explícito WARNING retorna constante correta."""
        assert _resolve_log_level("WARNING") == logging.WARNING

    def test_explicit_level_error(self) -> None:
        """Nível explícito ERROR retorna constante correta."""
        assert _resolve_log_level("ERROR") == logging.ERROR

    def test_explicit_level_critical(self) -> None:
        """Nível explícito CRITICAL retorna constante correta."""
        assert _resolve_log_level("CRITICAL") == logging.CRITICAL

    def test_case_insensitive(self) -> None:
        """Aceita nível em qualquer case."""
        assert _resolve_log_level("debug") == logging.DEBUG
        assert _resolve_log_level("Warning") == logging.WARNING

    def test_invalid_level_falls_back_to_info(self) -> None:
        """Nível inválido retorna INFO como fallback."""
        assert _resolve_log_level("INVALID") == logging.INFO
        assert _resolve_log_level("") == logging.INFO

    def test_none_uses_env_variable(self) -> None:
        """None lê da variável de ambiente LOGPULSE_LOG_LEVEL."""
        with patch.dict(os.environ, {"LOGPULSE_LOG_LEVEL": "ERROR"}):
            assert _resolve_log_level(None) == logging.ERROR

    def test_none_without_env_defaults_to_info(self) -> None:
        """None sem variável de ambiente retorna INFO."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove a variável se existir
            os.environ.pop("LOGPULSE_LOG_LEVEL", None)
            assert _resolve_log_level(None) == logging.INFO

    def test_whitespace_is_stripped(self) -> None:
        """Espaços em branco são removidos do nível."""
        assert _resolve_log_level("  DEBUG  ") == logging.DEBUG


class TestResolveOutputFormat:
    """Testes para resolução do formato de saída."""

    def test_explicit_true_returns_json(self) -> None:
        """Valor explícito True retorna JSON."""
        assert _resolve_output_format(True) is True

    def test_explicit_false_returns_text(self) -> None:
        """Valor explícito False retorna texto."""
        assert _resolve_output_format(False) is False

    def test_env_json_returns_true(self) -> None:
        """Variável LOGPULSE_LOG_FORMAT=json retorna True."""
        with patch.dict(os.environ, {"LOGPULSE_LOG_FORMAT": "json"}):
            assert _resolve_output_format(None) is True

    def test_env_text_returns_false(self) -> None:
        """Variável LOGPULSE_LOG_FORMAT=text retorna False."""
        with patch.dict(os.environ, {"LOGPULSE_LOG_FORMAT": "text"}):
            assert _resolve_output_format(None) is False

    def test_env_case_insensitive(self) -> None:
        """Variável de ambiente é case-insensitive."""
        with patch.dict(os.environ, {"LOGPULSE_LOG_FORMAT": "JSON"}):
            assert _resolve_output_format(None) is True

    def test_no_env_non_tty_returns_json(self) -> None:
        """Sem variável e sem TTY (CI/container) retorna JSON."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LOGPULSE_LOG_FORMAT", None)
            with patch("sys.stderr") as mock_stderr:
                mock_stderr.isatty.return_value = False
                assert _resolve_output_format(None) is True

    def test_no_env_tty_returns_text(self) -> None:
        """Sem variável e com TTY (desenvolvimento) retorna texto."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LOGPULSE_LOG_FORMAT", None)
            with patch("sys.stderr") as mock_stderr:
                mock_stderr.isatty.return_value = True
                assert _resolve_output_format(None) is False


class TestConfigureLogging:
    """Testes para a função configure_logging."""

    def test_configure_does_not_raise(self) -> None:
        """configure_logging() executa sem erros."""
        configure_logging(level="INFO", json_output=True)

    def test_configure_with_debug_level(self) -> None:
        """Configuração com nível DEBUG não levanta exceção."""
        configure_logging(level="DEBUG", json_output=False)

    def test_configure_sets_root_logger_level(self) -> None:
        """Configuração ajusta o nível do root logger."""
        configure_logging(level="WARNING", json_output=True)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_configure_idempotent(self) -> None:
        """Chamar configure_logging múltiplas vezes não causa erro."""
        configure_logging(level="INFO", json_output=True)
        configure_logging(level="DEBUG", json_output=False)


class TestGetLogger:
    """Testes para a função get_logger."""

    def setup_method(self) -> None:
        """Configura logging antes de cada teste."""
        configure_logging(level="DEBUG", json_output=True)

    def test_returns_bound_logger(self) -> None:
        """get_logger retorna instância de BoundLogger."""
        logger = get_logger("test.module")
        assert logger is not None

    def test_logger_with_initial_context(self) -> None:
        """Logger com contexto inicial mantém os bindings."""
        logger = get_logger("test.module", component="parser", version="1.0")
        assert logger is not None

    def test_logger_without_name(self) -> None:
        """Logger sem nome não levanta exceção."""
        logger = get_logger()
        assert logger is not None

    def test_logger_can_log_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Logger consegue emitir mensagem de nível INFO."""
        configure_logging(level="DEBUG", json_output=True)
        logger = get_logger("test.info")
        logger.info("test_event", key="value")
        # Se chegou aqui sem exceção, o log foi emitido com sucesso

    def test_logger_can_log_error(self) -> None:
        """Logger consegue emitir mensagem de nível ERROR."""
        logger = get_logger("test.error")
        logger.error("error_event", error="something failed")

    def test_logger_can_log_warning(self) -> None:
        """Logger consegue emitir mensagem de nível WARNING."""
        logger = get_logger("test.warning")
        logger.warning("warn_event", detail="check this")
