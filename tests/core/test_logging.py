"""Testes para o módulo de logging estruturado."""

import logging
from pathlib import Path

from src.core.logging import configure_logging, get_logger


def test_configure_logging_creates_file(tmp_path: Path) -> None:
    """Testa se configure_logging cria o arquivo de log."""
    log_file = tmp_path / "test.log"
    configure_logging(log_level="INFO", log_file=str(log_file))

    logger = get_logger(__name__)
    logger.info("test_message", key="value")

    assert log_file.exists()
    content = log_file.read_text()
    assert "test_message" in content


def test_configure_logging_sets_level() -> None:
    """Testa se configure_logging define o nível de log corretamente."""
    configure_logging(log_level="WARNING")

    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING


def test_get_logger_returns_structlog_logger() -> None:
    """Testa se get_logger retorna um logger estruturado."""
    logger = get_logger(__name__)

    # Verifica se o logger tem os métodos esperados
    assert hasattr(logger, "info")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


def test_logger_accepts_structured_data(tmp_path: Path) -> None:
    """Testa se o logger aceita dados estruturados."""
    log_file = tmp_path / "structured.log"
    configure_logging(log_level="INFO", log_file=str(log_file))

    logger = get_logger(__name__)
    logger.info(
        "operation_completed",
        user_id=123,
        action="upload",
        duration_ms=45.2,
    )

    content = log_file.read_text()
    assert "operation_completed" in content
    assert "user_id" in content
    assert "123" in content


def test_logger_handles_exceptions(tmp_path: Path) -> None:
    """Testa se o logger registra exceções corretamente."""
    log_file = tmp_path / "exceptions.log"
    configure_logging(log_level="ERROR", log_file=str(log_file))

    logger = get_logger(__name__)

    try:
        raise ValueError("Test error")
    except ValueError as exc:
        logger.error("error_occurred", error=str(exc), error_type=type(exc).__name__)

    content = log_file.read_text()
    assert "error_occurred" in content
    assert "Test error" in content
    assert "ValueError" in content


def test_log_rotation_configuration(tmp_path: Path) -> None:
    """Testa se a rotação de logs é configurada corretamente."""
    log_file = tmp_path / "rotation.log"
    max_bytes = 1024  # 1KB
    backup_count = 3

    configure_logging(
        log_level="INFO",
        log_file=str(log_file),
        max_bytes=max_bytes,
        backup_count=backup_count,
    )

    # Verifica se o handler de rotação foi configurado
    root_logger = logging.getLogger()
    rotating_handlers = [
        h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
    ]

    assert len(rotating_handlers) > 0
    handler = rotating_handlers[0]
    assert handler.maxBytes == max_bytes
    assert handler.backupCount == backup_count
