"""Router principal da API v1 do LogPulse IA.

Agrupa todos os endpoints de logs sob o prefixo /api/v1/logs.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.v1.routes.logs_routes import router as logs_router

router = APIRouter()
router.include_router(logs_router, prefix="/logs", tags=["logs"])
