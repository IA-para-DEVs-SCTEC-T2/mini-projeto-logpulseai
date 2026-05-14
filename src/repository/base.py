"""Interface abstrata para o repositório de logs do LogPulse IA.

Define o contrato que todas as implementações de persistência devem seguir,
garantindo que a camada de aplicação seja independente do mecanismo de storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.schemas import AIDiagnosis, AnalysisResult, LogAnalysisResponse


class LogRepository(ABC):
    """Interface abstrata para persistência de logs analisados.

    Define operações CRUD assíncronas que qualquer implementação concreta
    (SQLite, PostgreSQL, etc.) deve fornecer.

    Example:
        >>> class MyRepo(LogRepository):
        ...     async def create(self, content, analysis, diagnosis): ...
        ...     async def get_by_id(self, log_id): ...
        ...     async def list_paginated(self, page, page_size): ...
        ...     async def delete(self, log_id): ...
    """

    @abstractmethod
    async def create(
        self,
        content: str,
        analysis: AnalysisResult,
        diagnosis: AIDiagnosis,
    ) -> str:
        """Persiste um log analisado e retorna o UUID gerado.

        Args:
            content: Conteúdo bruto do log enviado pelo usuário.
            analysis: Resultado da análise de anomalias.
            diagnosis: Diagnóstico gerado pela IA.

        Returns:
            UUID (string) do registro criado.

        Raises:
            StorageError: Se a operação de escrita falhar.
        """

    @abstractmethod
    async def get_by_id(self, log_id: str) -> LogAnalysisResponse | None:
        """Recupera um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser recuperado.

        Returns:
            LogAnalysisResponse se encontrado, None caso contrário.

        Raises:
            StorageError: Se a operação de leitura falhar.
        """

    @abstractmethod
    async def list_paginated(
        self,
        page: int,
        page_size: int,
    ) -> list[LogAnalysisResponse]:
        """Lista logs com paginação, ordenados por data de criação (mais recente primeiro).

        Args:
            page: Número da página (começa em 1).
            page_size: Quantidade de itens por página.

        Returns:
            Lista de LogAnalysisResponse da página solicitada.

        Raises:
            StorageError: Se a operação de leitura falhar.
        """

    @abstractmethod
    async def delete(self, log_id: str) -> bool:
        """Remove um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser removido.

        Returns:
            True se o registro foi removido, False se não existia.

        Raises:
            StorageError: Se a operação de remoção falhar.
        """
