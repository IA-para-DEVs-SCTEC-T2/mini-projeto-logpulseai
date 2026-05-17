"""Endpoint de health check do LogPulse IA.

Verifica a saúde dos componentes: API, banco de dados e Ollama.
Retorna status "healthy" se tudo OK, "degraded" se algum componente falhar.

Referência: RF-12.4, RNF-08
"""

from __future__ import annotations

import socket
from typing import Any

import aiosqlite
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.core.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get(
    "/health",
    summary="Health check",
    description="Verifica a saúde da API, banco de dados e motor de IA (Ollama).",
    responses={
        200: {"description": "Sistema saudável ou degradado"},
    },
)
async def health_check() -> JSONResponse:
    """Verifica a saúde de todos os componentes do sistema.

    Componentes verificados:
    - **api**: sempre healthy (se este endpoint responde, a API está up)
    - **database**: tenta abrir conexão SQLite e executar query simples
    - **ollama**: tenta conectar na porta 11434 via TCP

    Returns:
        JSON com status geral ("healthy" ou "degraded") e detalhes
        de cada componente.

    Example:
        >>> GET /health
        {
            "status": "healthy",
            "components": {
                "api": {"status": "healthy"},
                "database": {"status": "healthy"},
                "ollama": {"status": "healthy"}
            }
        }
    """
    settings = get_settings()
    components: dict[str, dict[str, Any]] = {}

    # --- API ---
    components["api"] = {"status": "healthy"}

    # --- Database ---
    components["database"] = await _check_database(settings.database_url)

    # --- Ollama ---
    components["ollama"] = await _check_ollama(settings.ollama_base_url)

    # Status geral: degraded se qualquer componente não estiver healthy
    overall = (
        "healthy"
        if all(c["status"] == "healthy" for c in components.values())
        else "degraded"
    )

    http_status = 200
    return JSONResponse(
        status_code=http_status,
        content={"status": overall, "components": components},
    )


async def _check_database(db_path: str) -> dict[str, Any]:
    """Verifica conectividade com o banco de dados SQLite.

    Args:
        db_path: Caminho para o arquivo SQLite.

    Returns:
        Dict com status e mensagem opcional.
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as exc:
        logger.warning("health_check_database_failed", error=str(exc))
        return {"status": "unhealthy", "detail": "Banco de dados inacessível."}


async def _check_ollama(ollama_url: str) -> dict[str, Any]:
    """Verifica conectividade com o Ollama via TCP na porta 11434.

    Args:
        ollama_url: URL base do Ollama (ex: http://localhost:11434/v1).

    Returns:
        Dict com status e mensagem opcional.
    """
    try:
        # Extrai host e porta da URL
        host = "localhost"
        port = 11434
        if "://" in ollama_url:
            netloc = ollama_url.split("://")[1].split("/")[0]
            if ":" in netloc:
                host, port_str = netloc.rsplit(":", 1)
                port = int(port_str)
            else:
                host = netloc

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return {"status": "healthy"}
        else:
            return {
                "status": "unhealthy",
                "detail": f"Ollama não está acessível em {host}:{port}. Execute: ollama serve",
            }
    except Exception as exc:
        logger.warning("health_check_ollama_failed", error=str(exc))
        return {
            "status": "unhealthy",
            "detail": "Não foi possível verificar o Ollama. Execute: ollama serve",
        }
