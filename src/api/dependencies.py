"""Dependencias compartilhadas para injecao nos endpoints da API.

Fornece instancias de repositorio e outros servicos necessarios
pelos routers via FastAPI Depends.
"""

from __future__ import annotations

from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository

_repository: LogRepository | None = None


async def get_repository() -> LogRepository:
    """Retorna a instancia do repositorio de logs."""
    global _repository  # noqa: PLW0603
    if _repository is None:
        repo = SQLiteLogRepository()
        await repo.initialize()
        _repository = repo
    return _repository


def override_repository(repo: LogRepository) -> None:
    """Substitui o repositorio global (usado em testes)."""
    global _repository  # noqa: PLW0603
    _repository = repo
