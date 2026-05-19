"""Aplicação principal do LogPulse IA.

Este módulo inicializa a aplicação FastAPI com todos os routers,
middleware de logging e configurações necessárias.
"""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.logging import configure_logging, get_logger
from src.exceptions import (
    AIEngineTimeoutError,
    AIEngineUnavailableError,
    LogPulseError,
    ParsingError,
    StorageError,
)

# Configura logging estruturado
configure_logging(log_level="INFO", log_file="logpulse.log")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Gerencia o ciclo de vida da aplicação.

    Args:
        app: Instância da aplicação FastAPI.

    Yields:
        None durante a execução da aplicação.
    """
    logger.info("application_startup", version="0.1.0")
    yield
    logger.info("application_shutdown")


# Cria aplicação FastAPI
app = FastAPI(
    title="LogPulse IA",
    description="API REST para análise inteligente de logs com IA local (Ollama + LLaMA 3)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Middleware para logging estruturado de todas as requisições HTTP.

    Registra método, path, status code e duração de cada request.

    Args:
        request: Requisição HTTP recebida.
        call_next: Próximo middleware ou handler na cadeia.

    Returns:
        Response do handler.
    """
    start_time = time.time()

    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response

    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000

        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
            error=str(exc),
            duration_ms=round(duration_ms, 2),
        )
        raise


# Exception handlers para mapear exceções customizadas para HTTP status codes
@app.exception_handler(ParsingError)
async def parsing_error_handler(request: Request, exc: ParsingError) -> JSONResponse:
    """Handler para erros de parsing de logs."""
    logger.warning("parsing_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.exception_handler(AIEngineTimeoutError)
async def ai_timeout_error_handler(request: Request, exc: AIEngineTimeoutError) -> JSONResponse:
    """Handler para timeout do Ollama."""
    logger.error("ai_engine_timeout", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=504,
        content={"detail": str(exc)},
    )


@app.exception_handler(AIEngineUnavailableError)
async def ai_unavailable_error_handler(
    request: Request, exc: AIEngineUnavailableError
) -> JSONResponse:
    """Handler para Ollama indisponível."""
    logger.error("ai_engine_unavailable", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
    """Handler para erros de persistência."""
    logger.error("storage_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro de armazenamento: {exc}"},
    )


@app.exception_handler(LogPulseError)
async def logpulse_error_handler(request: Request, exc: LogPulseError) -> JSONResponse:
    """Handler genérico para erros do LogPulse."""
    logger.error(
        "logpulse_error", path=request.url.path, error_type=type(exc).__name__, error=str(exc)
    )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Endpoint de health check.

    Returns:
        Status da aplicação.
    """
    logger.debug("health_check_requested")
    return {"status": "healthy", "version": "0.1.0"}


# TODO: Registrar routers da API quando implementados
# from src.api.v1.logs.routes import router as logs_router
# app.include_router(logs_router, prefix="/api/v1/logs", tags=["Logs"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
