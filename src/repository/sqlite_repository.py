"""Implementação SQLite do repositório de logs do LogPulse IA.

Usa aiosqlite para operações assíncronas e serializa os modelos Pydantic
como JSON para armazenamento no banco de dados.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import aiosqlite

from src.core.logging import get_logger
from src.exceptions import StorageError
from src.models.schemas import AIDiagnosis, AnalysisResult, LogAnalysisResponse, SeverityLevel
from src.repository.base import LogRepository

logger = get_logger(__name__)

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

# Migração para adicionar colunas issues e recommended_actions
_ADD_ISSUES_COLUMN_SQL = """
ALTER TABLE logs ADD COLUMN issues TEXT;
"""

_ADD_RECOMMENDED_ACTIONS_COLUMN_SQL = """
ALTER TABLE logs ADD COLUMN recommended_actions TEXT;
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
        logger.info("repository_initialization_started", db_path=self._db_path)
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                await conn.execute(_CREATE_TABLE_SQL)
                await conn.execute(_CREATE_INDEX_SQL)
                
                # Migração: adiciona colunas issues e recommended_actions se não existirem
                try:
                    await conn.execute(_ADD_ISSUES_COLUMN_SQL)
                    logger.info("migration_add_issues_column_completed")
                except aiosqlite.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                    # Coluna já existe, ignora
                
                try:
                    await conn.execute(_ADD_RECOMMENDED_ACTIONS_COLUMN_SQL)
                    logger.info("migration_add_recommended_actions_column_completed")
                except aiosqlite.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                    # Coluna já existe, ignora
                
                await conn.commit()
            logger.info("repository_initialization_completed", db_path=self._db_path)
        except aiosqlite.Error as exc:
            logger.error(
                "repository_initialization_failed",
                db_path=self._db_path,
                error=str(exc)
            )
            raise StorageError(f"Falha ao inicializar banco de dados '{self._db_path}': {exc}") from exc

    async def create(
        self,
        content: str,
        analysis: AnalysisResult,
        diagnosis: AIDiagnosis,
        issues: list | None = None,
        recommended_actions: list[str] | None = None,
    ) -> str:
        """Persiste um log analisado e retorna o UUID gerado.

        Args:
            content: Conteúdo bruto do log enviado pelo usuário.
            analysis: Resultado da análise de anomalias.
            diagnosis: Diagnóstico gerado pela IA.
            issues: Lista de issues já calculados (opcional).
            recommended_actions: Lista de ações recomendadas (opcional).

        Returns:
            UUID (string) do registro criado.

        Raises:
            StorageError: Se a operação de escrita falhar.
        """
        import json
        
        log_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        analysis_json = analysis.model_dump_json()
        diagnosis_json = diagnosis.model_dump_json()
        
        # Serializa issues e recommended_actions como JSON
        issues_json = json.dumps([i.model_dump() for i in issues]) if issues else None
        actions_json = json.dumps(recommended_actions) if recommended_actions else None

        logger.info(
            "repository_create_started",
            log_id=log_id,
            content_length=len(content),
            total_entries=analysis.total_entries
        )

        try:
            async with aiosqlite.connect(self._db_path) as conn:
                await conn.execute(
                    """
                    INSERT INTO logs (id, content, analysis_result, ai_diagnosis, issues, recommended_actions, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (log_id, content, analysis_json, diagnosis_json, issues_json, actions_json, created_at),
                )
                await conn.commit()
            
            logger.info("repository_create_completed", log_id=log_id)
        except aiosqlite.Error as exc:
            logger.error(
                "repository_create_failed",
                log_id=log_id,
                error=str(exc)
            )
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
        logger.debug("repository_get_by_id_started", log_id=log_id)
        
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    "SELECT id, content, analysis_result, ai_diagnosis, issues, recommended_actions, created_at FROM logs WHERE id = ?",
                    (log_id,),
                ) as cursor:
                    row = await cursor.fetchone()
        except aiosqlite.Error as exc:
            logger.error(
                "repository_get_by_id_failed",
                log_id=log_id,
                error=str(exc)
            )
            raise StorageError(f"Falha ao recuperar log '{log_id}': {exc}") from exc

        if row is None:
            logger.debug("repository_get_by_id_not_found", log_id=log_id)
            return None

        logger.debug("repository_get_by_id_completed", log_id=log_id)
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

        logger.debug(
            "repository_list_paginated_started",
            page=page,
            page_size=page_size,
            offset=offset
        )

        try:
            async with aiosqlite.connect(self._db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(
                    """
                    SELECT id, content, analysis_result, ai_diagnosis, issues, recommended_actions, created_at
                    FROM logs
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (page_size, offset),
                ) as cursor:
                    rows = await cursor.fetchall()
        except aiosqlite.Error as exc:
            logger.error(
                "repository_list_paginated_failed",
                page=page,
                page_size=page_size,
                error=str(exc)
            )
            raise StorageError(f"Falha ao listar logs (page={page}, page_size={page_size}): {exc}") from exc

        # Converte para lista para permitir len()
        rows_list = list(rows)
        
        logger.debug(
            "repository_list_paginated_completed",
            page=page,
            page_size=page_size,
            results_count=len(rows_list)
        )

        return [self._row_to_response(row) for row in rows_list]

    async def count(self) -> int:
        """Retorna o total de registros no repositório.

        Returns:
            Número total de logs persistidos.

        Raises:
            StorageError: Se a operação de contagem falhar.
        """
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                async with conn.execute("SELECT COUNT(*) FROM logs") as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except aiosqlite.Error as exc:
            raise StorageError(f"Falha ao contar registros: {exc}") from exc

    async def delete(self, log_id: str) -> bool:
        """Remove um log pelo seu UUID.

        Args:
            log_id: UUID do registro a ser removido.

        Returns:
            True se o registro foi removido, False se não existia.

        Raises:
            StorageError: Se a operação de remoção falhar.
        """
        logger.info("repository_delete_started", log_id=log_id)
        
        try:
            async with aiosqlite.connect(self._db_path) as conn:
                cursor = await conn.execute(
                    "DELETE FROM logs WHERE id = ?",
                    (log_id,),
                )
                rows_affected = cursor.rowcount
                await conn.commit()
        except aiosqlite.Error as exc:
            logger.error(
                "repository_delete_failed",
                log_id=log_id,
                error=str(exc)
            )
            raise StorageError(f"Falha ao remover log '{log_id}': {exc}") from exc

        if rows_affected > 0:
            logger.info("repository_delete_completed", log_id=log_id)
        else:
            logger.debug("repository_delete_not_found", log_id=log_id)

        return rows_affected > 0

    @staticmethod
    def _row_to_response(row: aiosqlite.Row) -> LogAnalysisResponse:
        """Converte uma linha do banco de dados em LogAnalysisResponse.

        Args:
            row: Linha retornada pelo aiosqlite com campos id, content,
                 analysis_result, ai_diagnosis, issues, recommended_actions e created_at.

        Returns:
            LogAnalysisResponse desserializado.

        Raises:
            StorageError: Se a desserialização do JSON falhar.
        """
        import json
        from src.models.schemas import Issue
        
        try:
            analysis = AnalysisResult.model_validate_json(row["analysis_result"])
            diagnosis = AIDiagnosis.model_validate_json(row["ai_diagnosis"])
            
            # Desserializa issues se existir
            issues = []
            if row["issues"]:
                issues_data = json.loads(row["issues"])
                issues = [Issue.model_validate(i) for i in issues_data]
            
            # Desserializa recommended_actions se existir
            recommended_actions = []
            if row["recommended_actions"]:
                recommended_actions = json.loads(row["recommended_actions"])
                
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
            created_at = created_at.replace(tzinfo=UTC)

        # Calcula métricas
        metrics = {
            "total_logs": analysis.total_entries,
            "errors": analysis.severity_distribution.get(SeverityLevel.ERROR, 0),
            "criticals": analysis.severity_distribution.get(SeverityLevel.CRITICAL, 0)
        }

        # Constrói resposta diretamente
        return LogAnalysisResponse(
            id=row["id"],
            analyzed_at=created_at,
            metrics=metrics,
            issues=issues,
            recommended_actions=recommended_actions,
            confidence=diagnosis.confidence
        )
