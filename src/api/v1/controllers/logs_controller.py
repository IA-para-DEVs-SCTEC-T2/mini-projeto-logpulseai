"""Controller de logs — orquestra validação e delega aos services.

Padrão MVC completo:
  Route (View) → Controller → Service → Repository (Model)

O controller é responsável por:
  1. Validação de entrada (extensão, conteúdo vazio)
  2. Delegação ao service correto
  3. Tradução de erros de domínio para HTTPException

Os services encapsulam a lógica de negócio:
  - LogAnalysisService: pipeline parse → analyze → diagnose → persist
  - LogStorageService: operações CRUD (list, get, delete)

Referências: RF-01, RF-02, RF-06
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from src.core.logging import get_logger
from src.exceptions import NotFoundError, ParsingError, StorageError
from src.models.schemas import (
    LogAnalysisResponse,
    LogListResponse,
    LogTextUpload,
)
from src.services.log_analysis_service import LogAnalysisService
from src.services.log_storage_service import LogStorageService

logger = get_logger(__name__)

# Extensões permitidas para upload
_ALLOWED_EXTENSIONS = (".log", ".txt")


class LogsController:
    """Controller responsável pela lógica dos endpoints de logs.

    Recebe os services injetados e orquestra o fluxo de cada operação.
    Não contém lógica de negócio — apenas validação de entrada e
    tradução de exceções para respostas HTTP.

    Args:
        analysis_service: Serviço de análise (pipeline completo).
        storage_service: Serviço de CRUD (listagem, consulta, remoção).
    """

    def __init__(
        self,
        analysis_service: LogAnalysisService,
        storage_service: LogStorageService,
    ) -> None:
        """Inicializa o controller com os services."""
        self._analysis_service = analysis_service
        self._storage_service = storage_service

    async def upload_file(self, file: UploadFile) -> LogAnalysisResponse:
        """Processa upload de arquivo de log.

        Valida extensão e conteúdo, delega ao LogAnalysisService.

        Args:
            file: Arquivo enviado via multipart/form-data.

        Returns:
            LogAnalysisResponse com análise e diagnóstico.

        Raises:
            HTTPException 415: Formato de arquivo não suportado.
            HTTPException 422: Arquivo vazio.
        """
        filename = file.filename or ""
        logger.info("upload_file_request", filename=filename, content_type=file.content_type)

        # Validação de extensão
        if not filename.lower().endswith(_ALLOWED_EXTENSIONS):
            logger.warning("upload_file_rejected", filename=filename, reason="invalid_extension")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Formato de arquivo não suportado. Apenas {_ALLOWED_EXTENSIONS} são aceitos.",
            )

        # Leitura do conteúdo
        content = (await file.read()).decode("utf-8", errors="replace")
        logger.info("upload_file_read", filename=filename, content_length=len(content))

        # Validação de conteúdo
        if not content.strip():
            logger.warning("upload_file_rejected", filename=filename, reason="empty_content")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Arquivo vazio ou sem conteúdo válido.",
            )

        # Delega ao service
        response = await self._analysis_service.analyze_content(content)

        logger.info(
            "upload_file_success",
            filename=filename,
            log_id=response.id,
            total_logs=response.metrics.get("total_logs", 0),
        )
        return response

    async def upload_text(self, payload: LogTextUpload) -> LogAnalysisResponse:
        """Processa envio de log via texto puro.

        Args:
            payload: Body com campo 'content'.

        Returns:
            LogAnalysisResponse com análise e diagnóstico.
        """
        logger.info("upload_text_request", content_length=len(payload.content))

        # Delega ao service
        response = await self._analysis_service.analyze_content(payload.content)

        logger.info(
            "upload_text_success",
            log_id=response.id,
            total_logs=response.metrics.get("total_logs", 0),
        )
        return response

    async def list_logs(self, page: int = 1, page_size: int = 20) -> LogListResponse:
        """Lista logs com paginação.

        Args:
            page: Número da página (≥1).
            page_size: Itens por página (1-100).

        Returns:
            LogListResponse com itens e metadados de paginação.
        """
        return await self._storage_service.list_logs(page, page_size)

    async def get_by_id(self, log_id: str) -> LogAnalysisResponse:
        """Recupera um log pelo ID.

        Args:
            log_id: UUID do registro.

        Returns:
            LogAnalysisResponse.

        Raises:
            HTTPException 404: Log não encontrado.
        """
        record = await self._storage_service.get_by_id(log_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log '{log_id}' não encontrado.",
            )
        return record

    async def delete(self, log_id: str) -> None:
        """Remove um log pelo ID.

        Args:
            log_id: UUID do registro.

        Raises:
            HTTPException 404: Log não encontrado.
        """
        deleted = await self._storage_service.delete_log(log_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log '{log_id}' não encontrado.",
            )
