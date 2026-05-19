"""Aplicação FastAPI principal do LogPulse IA.

Configura a aplicação com:
- CORS para permitir acesso de origens externas
- Middleware de tratamento centralizado de erros
- Routers v1 registrados com prefixo /api/v1
- Health check em /health
- Swagger UI em /docs e ReDoc em /redoc

Referências: RF-07.5, RF-08.1, RF-08.2, RF-08.3, RF-08.4, RNF-05, RNF-08
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.health import router as health_router
from src.api.middleware import register_exception_handlers
from src.api.v1.router import router as v1_router
from src.core.config import get_settings
from src.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia o ciclo de vida da aplicação.

    Startup: configura logging estruturado.
    Shutdown: libera recursos se necessário.
    """
    configure_logging()
    logger.info("logpulse_startup", version=app.version)
    yield
    logger.info("logpulse_shutdown")


def create_app() -> FastAPI:
    """Factory para criação da aplicação FastAPI.

    Configura título, versão, CORS, middleware de erros,
    documentação e registra todos os routers.

    Returns:
        Instância configurada do FastAPI.

    Example:
        >>> app = create_app()
        >>> # Iniciar com: uvicorn src.api.app:app --reload
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=(
            "API REST para análise inteligente de logs com IA local (Ollama + LLaMA 3). "
            "Envie logs via arquivo ou texto e receba diagnóstico estruturado com causa raiz e ações corretivas."
        ),
        debug=settings.api_debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # --- CORS ---
    # Permite acesso de qualquer origem em desenvolvimento.
    # Em produção, substituir por lista explícita de origens permitidas.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception handlers (antes dos routers) ---
    register_exception_handlers(app)

    # --- Routers ---
    app.include_router(health_router)           # GET /health
    app.include_router(v1_router, prefix="/api/v1")  # /api/v1/logs/*

    return app


# Instância global para uvicorn
app = create_app()
