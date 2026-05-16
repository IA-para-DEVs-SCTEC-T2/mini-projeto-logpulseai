
"""Dependências compartilhadas para injeção nos endpoints da API.

Fornece instâncias de repositório e outros serviços necessários

"""Dependências compartilhadas para injeção nos endpoints da API.

Fornece instâncias de repositório e outros serviços necessários
"""Dependencias compartilhadas para injecao nos endpoints da API.

Fornece instancias de repositorio e outros servicos necessarios
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
    """Retorna a instancia do repositorio de logs."""
    global _repository  # noqa: PLW0603
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
    """Substitui o repositorio global (usado em testes)."""
    global _repository  # noqa: PLW0603
    _repository = repo
