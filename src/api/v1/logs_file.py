"""Router para endpoint POST /api/v1/logs/file.

Endpoint para upload de arquivo de log (.log ou .txt),
processamento via pipeline (parse → analyze → diagnose) e persistência.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from src.ai.base import AIEngine
from src.ai.ollama_engine import OllamaAIEngine
from src.analyzer.detector import AnomalyDetector
from src.api.dependencies import get_repository
from src.exceptions import AIEngineTimeoutError, AIEngineUnavailableError
from src.models.schemas import LogAnalysisResponse, LogFileUpload
from src.parsers.drain3_parser import Drain3LogParser
from src.repository.base import LogRepository

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

# Extensões permitidas para upload
_ALLOWED_EXTENSIONS = (".log", ".txt")

# Tamanho máximo do arquivo (50 MB)
_MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post(
    "/file",
    response_model=LogAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de arquivo de log",
    description="Recebe um arquivo .log ou .txt, processa via pipeline de análise e retorna diagnóstico.",
    responses={
        400: {"description": "Arquivo inválido (extensão ou tamanho)"},
        503: {"description": "Motor de IA indisponível"},
    },
)
async def upload_log_file(
    file: UploadFile,
    repository: LogRepository = Depends(get_repository),
) -> LogAnalysisResponse:
    """Processa upload de arquivo de log.

    Pipeline: validação → parse → análise → diagnóstico IA → persistência.

    Args:
        file: Arquivo enviado via multipart/form-data.
        repository: Instância do repositório injetada via Depends.

    Returns:
        LogAnalysisResponse com análise e diagnóstico completos.

    Raises:
        HTTPException 400: Se o arquivo for inválido (extensão ou tamanho).
        HTTPException 503: Se o motor de IA estiver indisponível.
    """
    # Validação do nome do arquivo
    filename = file.filename or ""
    if not filename.lower().endswith(_ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Apenas arquivos {_ALLOWED_EXTENSIONS} são aceitos. Recebido: '{filename}'",
        )

    # Leitura do conteúdo
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8", errors="replace")

    # Validação de tamanho
    if len(content_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo excede o limite de 50MB. Tamanho: {len(content_bytes)} bytes",
        )

    # Validação de conteúdo não vazio
    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo está vazio ou contém apenas espaços em branco",
        )

    # Validação via schema Pydantic
    LogFileUpload(filename=filename, content=content)

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
