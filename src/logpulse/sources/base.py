"""Interface base para fontes de log."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator


class LogSource(ABC):
    """Interface abstrata para adaptadores de leitura de logs."""

    @abstractmethod
    def read_lines(self) -> Iterator[str]:
        """Lê e retorna linhas brutas da fonte de log."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Libera recursos associados à fonte."""
        ...

    def __enter__(self) -> "LogSource":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
