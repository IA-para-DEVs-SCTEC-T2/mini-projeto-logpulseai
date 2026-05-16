"""Configuração de logging estruturado do LogPulse IA.

Utiliza structlog para produzir logs em formato JSON estruturado,
facilitando integração com ferramentas de observabilidade e
análise automatizada de logs internos do sistema.

O módulo expõe duas funções principais:
- `configure_logging()`: Configura o structlog globalmente (chamar uma vez na inicialização).
- `get_logger()`: Retorna um logger bound com contexto opcional.

Example:
    >>> from src.core.logging import configure_logging, get_logger
    >>> configure_logging()
    >>> logger = get_logger("src.parsers.drain3_parser")
    >>> logger.info("parsing_started", file="app.log", lines=1500)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog


def configure_logging(
    level: str | None = None,
    json_output: bool | None = None,
) -> None:
    """Configura o sistema de logging estruturado globalmente.

    Deve ser chamada uma única vez durante a inicialização da aplicação
    (ex: no startup do FastAPI ou no entrypoint da CLI).

    Args:
        level: Nível mínimo de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Se não informado, usa a variável de ambiente LOGPULSE_LOG_LEVEL
            ou o padrão INFO.
        json_output: Se True, produz saída JSON. Se False, usa formato
            legível para desenvolvimento. Se None, usa a variável de
            ambiente LOGPULSE_LOG_FORMAT (json|text) ou detecta
            automaticamente (JSON se não for terminal interativo).
    """
    log_level = _resolve_log_level(level)
    use_json = _resolve_output_format(json_output)

    # Configura o logging stdlib para capturar logs de bibliotecas terceiras
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # Processadores compartilhados (pre-chain para logs stdlib e structlog)
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if use_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    # Configura structlog para usar stdlib LoggerFactory
    # Isso permite que add_logger_name funcione corretamente
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    # Configura o formatter para loggers stdlib (uvicorn, httpx, etc.)
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str | None = None, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado com contexto inicial opcional.

    Args:
        name: Nome do logger (geralmente __name__ do módulo).
        **initial_context: Pares chave-valor para contexto permanente
            do logger (ex: component="parser", version="1.0").

    Returns:
        Logger bound do structlog pronto para uso.

    Example:
        >>> logger = get_logger("src.ai.ollama_engine", model="llama3")
        >>> logger.info("request_sent", tokens=150)
        # Produz: {"event": "request_sent", "logger": "src.ai.ollama_engine",
        #          "model": "llama3", "tokens": 150, ...}
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger  # type: ignore[return-value]


def _resolve_log_level(level: str | None) -> int:
    """Resolve o nível de log a partir do parâmetro ou variável de ambiente.

    Args:
        level: Nível explícito ou None para usar env/default.

    Returns:
        Constante numérica do logging stdlib.
    """
    if level is None:
        level = os.environ.get("LOGPULSE_LOG_LEVEL", "INFO")

    level_upper = level.upper().strip()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    if level_upper not in valid_levels:
        # Fallback seguro para INFO se valor inválido
        return logging.INFO

    return getattr(logging, level_upper)


def _resolve_output_format(json_output: bool | None) -> bool:
    """Resolve o formato de saída (JSON vs texto legível).

    Args:
        json_output: Valor explícito ou None para auto-detecção.

    Returns:
        True para JSON, False para texto legível.
    """
    if json_output is not None:
        return json_output

    env_format = os.environ.get("LOGPULSE_LOG_FORMAT", "").lower().strip()
    if env_format == "json":
        return True
    if env_format == "text":
        return False

    # Auto-detecção: JSON se não for terminal interativo (ex: container, CI)
    return not sys.stderr.isatty()
