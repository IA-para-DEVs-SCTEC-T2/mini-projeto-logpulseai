"""Implementação SQLite do repositório de logs do LogPulse IA.

Usa aiosqlite para operações assíncronas e serializa os modelos Pydantic
como JSON para armazenamento no banco de dados.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import aiosqlite

from src.exceptions import StorageError
from src.models.schemas import AIDiagnosis, AnalysisResult, LogAnalysisResponse
from src.repository.base import LogRepository

# DDL executado na inicialização do repositório
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS logs (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    analysis_result TEXT NOT NULL,
    ai_diagnosis TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
"""


class SQLiteLogRepository(LogRepository):
    """Repositório de logs persistido em banco de dados SQLite.

    Utiliza aiosqlite para operações assíncronas não bloqueantes.
    Os modelos AnalysisResult e AIDiagnosis são serializados como JSON
    usando os métodos nativos do Pydantic.

    Args:
        db_path: Caminho para o arquivo SQLite. Padrão: "logpulse.db".

    Example:
        >>> repo = SQLiteLogRepository(db_path=":memory:")
        >>> await repo.initialize()
        >>> log_id = await repo.create(content, analysis, diagnosis)
        >>> record = await repo.get_by_id(log_id)
    """

    def __init__(self, db_path: str = "logpulse.db") -> None:
        """Inicializa o repositório com o caminho do banco de dados.

        Args:
            db_path: Caminho para o arquivo SQLite. Use ":memory:" para banco em memória.
        """
        self._db_path = db_path

    async def initialize(self) -> None:
        """Cria a tabela e o índice se ainda não existirem.

        Deve ser chamado uma vez antes de usar o repositório.

        Raises:
            StorageError: Se a criação da tabela ou índice falhar.
        """
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                await conn.execute(_CREATE_TABLE_SQL)
                await conn.execute(_CREATE_INDEX_SQL)
                await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(f"Falha ao inicializar banco de dados '{self._db_path}': {exc}") from exc

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
        log_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        analysis_json = analysis.model_dump_json()
        diagnosis_json = diagnosis.model_dump_json()

        try:
            async with aiosqlite.connect(self._db_path) as conn:
                await conn.execute(
                    """
                    INSERT INTO logs (id, content, analysis_result, ai_diagnosis, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (log_id, content, analysis_json, diagnosis_json, created_at),
                )
                await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(f"Falha ao criar registro de log: {exc}") from exc

        return log_id

    async def get_by_id(self, log_id: str) -> LogAnalysisResponse | None:
        """Recupera um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser recuperado.

        Returns:
            LogAnalysisResponse se encontrado, None caso contrário.

        Raises:
            StorageError: Se a operação de leitura falhar.
        """
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    "SELECT id, content, analysis_result, ai_diagnosis, created_at FROM logs WHERE id = ?",
                    (log_id,),
                ) as cursor:
                    row = await cursor.fetchone()
        except aiosqlite.Error as exc:
            raise StorageError(f"Falha ao recuperar log '{log_id}': {exc}") from exc

        if row is None:
            return None

        return self._row_to_response(row)

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
        offset = (page - 1) * page_size

        try:
            async with aiosqlite.connect(self._db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    """
                    SELECT id, content, analysis_result, ai_diagnosis, created_at
                    FROM logs
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (page_size, offset),
                ) as cursor:
                    rows = await cursor.fetchall()
        except aiosqlite.Error as exc:
            raise StorageError(f"Falha ao listar logs (page={page}, page_size={page_size}): {exc}") from exc

        return [self._row_to_response(row) for row in rows]

    async def delete(self, log_id: str) -> bool:
        """Remove um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser removido.

        Returns:
            True se o registro foi removido, False se não existia.

        Raises:
            StorageError: Se a operação de remoção falhar.
        """
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                cursor = await conn.execute(
                    "DELETE FROM logs WHERE id = ?",
                    (log_id,),
                )
                rows_affected = cursor.rowcount
                await conn.commit()
        except aiosqlite.Error as exc:
            raise StorageError(f"Falha ao remover log '{log_id}': {exc}") from exc

        return rows_affected > 0

    @staticmethod
    def _row_to_response(row: aiosqlite.Row) -> LogAnalysisResponse:
        """Converte uma linha do banco de dados em LogAnalysisResponse.

        Args:
            row: Linha retornada pelo aiosqlite com campos id, content,
                 analysis_result, ai_diagnosis e created_at.

        Returns:
            LogAnalysisResponse desserializado.

        Raises:
            StorageError: Se a desserialização do JSON falhar.
        """
        try:
            analysis = AnalysisResult.model_validate_json(row["analysis_result"])
            diagnosis = AIDiagnosis.model_validate_json(row["ai_diagnosis"])
        except Exception as exc:
            raise StorageError(
                f"Falha ao desserializar dados do log '{row['id']}': {exc}"
            ) from exc

        # Garante que created_at tem timezone UTC
        raw_ts = row["created_at"]
        if isinstance(raw_ts, str):
            created_at = datetime.fromisoformat(raw_ts)
        else:
            created_at = raw_ts

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        return LogAnalysisResponse(
            id=row["id"],
            analysis=analysis,
            diagnosis=diagnosis,
            created_at=created_at,
            total_entries=analysis.total_entries,
            summary=diagnosis.summary,
        )
