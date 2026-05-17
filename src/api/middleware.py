"""Middleware e handlers de exceções do LogPulse IA.

Registra exception handlers no FastAPI para mapear exceções do domínio
para respostas HTTP padronizadas com campo `detail` e logging estruturado.

Mapeamento de exceções → HTTP status codes:
    ParsingError            → 422 Unprocessable Entity
    ValidationError         → 422 Unprocessable Entity
    NotFoundError           → 404 Not Found
    AIEngineUnavailableError → 503 Service Unavailable
    AIEngineTimeoutError    → 504 Gateway Timeout
    AIEngineError           → 502 Bad Gateway
    StorageError            → 500 Internal Server Error
    AnalysisError           → 500 Internal Server Error
    ConfigError             → 500 Internal Server Error
    LogPulseError (base)    → 500 Internal Server Error
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.core.logging import get_logger
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

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos os exception handlers na aplicação FastAPI.

    Deve ser chamada durante a criação da aplicação, antes de iniciar
    o servidor. Os handlers são registrados do mais específico para o
    mais genérico, garantindo que subclasses sejam tratadas primeiro.

    Args:
        app: Instância do FastAPI onde os handlers serão registrados.

    Example:
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    # Handlers específicos de AIEngine (subclasses antes da classe base)
    app.add_exception_handler(AIEngineUnavailableError, _handle_ai_unavailable)
    app.add_exception_handler(AIEngineTimeoutError, _handle_ai_timeout)
    app.add_exception_handler(AIEngineError, _handle_ai_engine_error)

    # Handlers de validação e busca
    app.add_exception_handler(ParsingError, _handle_parsing_error)
    app.add_exception_handler(ValidationError, _handle_validation_error)
    app.add_exception_handler(NotFoundError, _handle_not_found_error)

    # Handlers de infraestrutura
    app.add_exception_handler(StorageError, _handle_storage_error)
    app.add_exception_handler(AnalysisError, _handle_analysis_error)
    app.add_exception_handler(ConfigError, _handle_config_error)

    # Handler base (captura qualquer LogPulseError não tratada acima)
    app.add_exception_handler(LogPulseError, _handle_logpulse_error)


# ---------------------------------------------------------------------------
# Handlers individuais
# ---------------------------------------------------------------------------


async def _handle_ai_unavailable(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia AIEngineUnavailableError → HTTP 503 Service Unavailable."""
    logger.error(
        "ai_engine_unavailable",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc) or "Motor de IA indisponível. Verifique se o Ollama está em execução na porta 11434."},
    )


async def _handle_ai_timeout(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia AIEngineTimeoutError → HTTP 504 Gateway Timeout."""
    logger.error(
        "ai_engine_timeout",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": str(exc) or "Motor de IA não respondeu dentro do tempo limite de 30 segundos."},
    )


async def _handle_ai_engine_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia AIEngineError genérico → HTTP 502 Bad Gateway."""
    logger.error(
        "ai_engine_error",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc) or "Erro ao comunicar com o motor de IA."},
    )


async def _handle_parsing_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia ParsingError → HTTP 422 Unprocessable Entity."""
    logger.warning(
        "parsing_error",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc) or "Erro ao processar o conteúdo do log."},
    )


async def _handle_validation_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia ValidationError → HTTP 422 Unprocessable Entity."""
    logger.warning(
        "validation_error",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc) or "Dados de entrada inválidos."},
    )


async def _handle_not_found_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia NotFoundError → HTTP 404 Not Found."""
    logger.info(
        "not_found",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc) or "Recurso não encontrado."},
    )


async def _handle_storage_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia StorageError → HTTP 500 Internal Server Error."""
    logger.error(
        "storage_error",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno ao acessar o banco de dados."},
    )


async def _handle_analysis_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia AnalysisError → HTTP 500 Internal Server Error."""
    logger.error(
        "analysis_error",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno durante a análise do log."},
    )


async def _handle_config_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia ConfigError → HTTP 500 Internal Server Error."""
    logger.error(
        "config_error",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro de configuração interna do servidor."},
    )


async def _handle_logpulse_error(
    request: Request, exc: Exception
) -> JSONResponse:
    """Mapeia LogPulseError genérica → HTTP 500 Internal Server Error.

    Handler de fallback para qualquer exceção do domínio não capturada
    pelos handlers mais específicos acima.
    """
    logger.error(
        "logpulse_error_unhandled",
        path=request.url.path,
        method=request.method,
        detail=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor."},
    )
