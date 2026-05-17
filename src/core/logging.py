"""Configuração de logging estruturado para o LogPulse IA.

Este módulo configura o structlog para logging estruturado em JSON,
com handlers para console e arquivo com rotação.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog


def configure_logging(
    log_level: str = "INFO",
    log_file: str = "logpulse.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """Configura o sistema de logging estruturado.

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Caminho do arquivo de log.
        max_bytes: Tamanho máximo do arquivo antes da rotação (padrão: 10MB).
        backup_count: Número de arquivos de backup a manter (padrão: 5).

    Example:
        >>> configure_logging(log_level="DEBUG", log_file="app.log")
    """
    # Converte string para nível de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configura o logger raiz do Python
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove handlers existentes para evitar duplicação
    root_logger.handlers.clear()

    # Handler para console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Handler para arquivo com rotação
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)

    # Adiciona handlers ao logger raiz
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configura structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Renderiza como JSON para arquivo, mas formato legível para console
            structlog.processors.JSONRenderer() if log_file else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Obtém um logger estruturado.

    Args:
        name: Nome do logger (geralmente __name__ do módulo).

    Returns:
        Logger estruturado do structlog.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("operation_started", user_id=123, action="upload")
    """
    return structlog.get_logger(name)
