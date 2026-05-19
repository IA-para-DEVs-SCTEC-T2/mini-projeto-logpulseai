"""Dependências compartilhadas para injeção nos endpoints da API.

Fornece instâncias de repositório e outros serviços necessários
pelos routers via FastAPI Depends.
"""

from __future__ import annotations

from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository

_repository: LogRepository | None = None


async def get_repository() -> LogRepository:
    """Retorna a instância do repositório de logs.

    Inicializa o repositório na primeira chamada (singleton).

    Returns:
        Instância de LogRepository pronta para uso.
    """
    global _repository
    if _repository is None:
        repo = SQLiteLogRepository()
        await repo.initialize()
        _repository = repo
    return _repository


def override_repository(repo: LogRepository) -> None:
    """Substitui o repositório global (usado em testes).

    Args:
        repo: Instância de LogRepository para substituir o padrão.
    """
    global _repository
    _repository = repo
