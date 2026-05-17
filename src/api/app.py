"""Aplicação FastAPI principal do LogPulse IA.

Configura a aplicação, registra routers e define eventos de lifecycle.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.middleware import register_exception_handlers
from src.api.v1.router import router as v1_router
from src.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia o ciclo de vida da aplicação.

    Executa inicializações no startup e limpeza no shutdown.
    """
    # Startup: inicializa recursos compartilhados
    yield
    # Shutdown: libera recursos se necessário


def create_app() -> FastAPI:
    """Factory para criação da aplicação FastAPI.

    Configura título, versão, documentação e registra routers.
    Permite criação de múltiplas instâncias para testes.

    Returns:
        Instância configurada do FastAPI.

    Example:
        >>> app = create_app()
        >>> # Usar com uvicorn: uvicorn src.api.app:app
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="API REST para análise inteligente de logs com IA local (Ollama + LLaMA 3)",
        debug=settings.api_debug,
        lifespan=lifespan,
    )

    # Registra handlers de exceções do domínio (antes dos routers)
    register_exception_handlers(app)

    # Registra router v1
    app.include_router(v1_router, prefix="/api/v1")

    return app


# Instância global para uvicorn
app = create_app()
