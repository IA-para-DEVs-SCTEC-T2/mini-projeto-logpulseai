"""Router para endpoint POST /api/v1/logs/text.

Endpoint para envio de log via texto puro,
processamento via pipeline (parse → analyze → diagnose) e persistência.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.ai.base import AIEngine
from src.ai.ollama_engine import OllamaAIEngine
from src.analyzer.detector import AnomalyDetector
from src.api.dependencies import get_repository
from src.exceptions import AIEngineTimeoutError, AIEngineUnavailableError
from src.models.schemas import LogAnalysisResponse, LogTextUpload
from src.parsers.drain3_parser import Drain3LogParser
from src.repository.base import LogRepository

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.post(
    "/text",
    response_model=LogAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Envio de log via texto",
    description="Recebe conteúdo de log em texto puro, processa via pipeline de análise e retorna diagnóstico.",
    responses={
        400: {"description": "Conteúdo inválido (vazio ou excede limite)"},
        503: {"description": "Motor de IA indisponível"},
    },
)
async def upload_log_text(
    payload: LogTextUpload,
    repository: LogRepository = Depends(get_repository),
) -> LogAnalysisResponse:
    """Processa envio de log via texto.

    Pipeline: validação → parse → análise → diagnóstico IA → persistência.

    Args:
        payload: Body JSON com campo 'content' contendo o log em texto.
        repository: Instância do repositório injetada via Depends.

    Returns:
        LogAnalysisResponse com análise e diagnóstico completos.

    Raises:
        HTTPException 400: Se o conteúdo for inválido.
        HTTPException 503: Se o motor de IA estiver indisponível.
    """
    content = payload.content

    # Validação de conteúdo não vazio (após strip)
    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conteúdo está vazio ou contém apenas espaços em branco",
        )

    # Pipeline: parse → analyze → diagnose
    parser = Drain3LogParser()
    entries = parser.parse(content)
    templates = parser.get_templates()

    analyzer = AnomalyDetector()
    analysis = analyzer.analyze(entries, templates)

    # Diagnóstico IA
    try:
        engine: AIEngine = OllamaAIEngine()
        diagnosis = engine.diagnose(analysis, entries)
    except AIEngineUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor de IA indisponível: {exc}",
        ) from exc
    except AIEngineTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Motor de IA não respondeu: {exc}",
        ) from exc

    # Persistência
    log_id = await repository.create(content, analysis, diagnosis)

    # Recupera registro completo para resposta
    result = await repository.get_by_id(log_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao recuperar registro após criação",
        )

    return result
