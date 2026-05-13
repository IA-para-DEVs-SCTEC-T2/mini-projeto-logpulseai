"""Camada de persistência do LogPulse IA.

Expõe a interface abstrata LogRepository e a implementação SQLiteLogRepository.
"""

from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository

__all__ = [
    "LogRepository",
    "SQLiteLogRepository",
]
