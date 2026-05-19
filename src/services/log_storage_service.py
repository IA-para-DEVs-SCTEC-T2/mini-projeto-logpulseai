"""Serviço de armazenamento de logs — operações CRUD.

Encapsula operações de leitura, listagem e remoção de logs persistidos.

Referências: RF-06.2, RF-06.4, RF-06.5
"""

from __future__ import annotations

import logging
import math

from src.exceptions import StorageError
from src.models.schemas import LogAnalysisResponse, LogListResponse
from src.repository.base import LogRepository

logger = logging.getLogger(__name__)


class LogStorageService:
    """Serviço para operações de consulta e remoção de logs.

    Encapsula a lógica de negócio para operações CRUD de leitura
    e deleção, incluindo paginação e cálculo de metadados.

    Args:
        repository: Implementação de LogRepository para persistência.

    Example:
        >>> service = LogStorageService(repo)
        >>> response = await service.get_by_id("uuid-123")
        >>> logs = await service.list_logs(page=1, page_size=20)
    """

    def __init__(self, repository: LogRepository) -> None:
        """Inicializa o serviço com o repositório injetado."""
        self._repository = repository

    async def get_by_id(self, log_id: str) -> LogAnalysisResponse | None:
        """Recupera um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser recuperado.

        Returns:
            LogAnalysisResponse se encontrado, None caso contrário.

        Raises:
            StorageError: Se a operação de leitura falhar.
        """
        logger.debug("Buscando log por ID: %s", log_id)
        try:
            return await self._repository.get_by_id(log_id)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(
                f"Falha ao buscar log '{log_id}': {exc}"
            ) from exc

    async def list_logs(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> LogListResponse:
        """Lista logs com paginação e metadados.

        Args:
            page: Número da página (começa em 1).
            page_size: Quantidade de itens por página (1-100).

        Returns:
            LogListResponse com itens, total, página atual e total de páginas.

        Raises:
            StorageError: Se a operação de leitura falhar.
            ValueError: Se page < 1 ou page_size fora do intervalo [1, 100].
        """
        if page < 1:
            raise ValueError("page deve ser >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size deve estar entre 1 e 100")

        logger.debug("Listando logs: page=%d, page_size=%d", page, page_size)

        try:
            items = await self._repository.list_paginated(page, page_size)
            total = await self._get_total_count()
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(
                f"Falha ao listar logs (page={page}, page_size={page_size}): {exc}"
            ) from exc

        pages = math.ceil(total / page_size) if total > 0 else 0

        return LogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def delete_log(self, log_id: str) -> bool:
        """Remove um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser removido.

        Returns:
            True se o registro foi removido, False se não existia.

        Raises:
            StorageError: Se a operação de remoção falhar.
        """
        logger.info("Removendo log: %s", log_id)
        try:
            return await self._repository.delete(log_id)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(
                f"Falha ao remover log '{log_id}': {exc}"
            ) from exc

    async def _get_total_count(self) -> int:
        """Obtém o total de registros no repositório.

        Usa list_paginated com page_size grande para estimar o total.
        Implementações futuras podem adicionar método count() ao repositório.

        Returns:
            Total estimado de registros.
        """
        # Estratégia: busca página 1 com tamanho grande para contar
        # Nota: idealmente o repositório teria um método count()
        # Por ora, usamos uma abordagem pragmática
        all_items = await self._repository.list_paginated(page=1, page_size=10000)
        return len(all_items)
