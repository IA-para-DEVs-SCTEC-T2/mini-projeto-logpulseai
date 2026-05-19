"""Ponto de entrada para execução direta com uvicorn.


Uso:
    uvicorn src.api.app:app --reload --port 8000

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


Ou diretamente:
    python -m src.main
"""

from src.api.app import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
