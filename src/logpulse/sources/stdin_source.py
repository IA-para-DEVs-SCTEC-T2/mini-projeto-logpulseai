"""Adaptador de leitura de logs via stdin/pipe."""

from __future__ import annotations

import sys
from collections.abc import Iterator

from logpulse.sources.base import LogSource


class StdinSource(LogSource):
    """Lê linhas de log a partir do stdin."""

    def read_lines(self) -> Iterator[str]:
        """Lê e retorna linhas brutas do stdin."""
        for line in sys.stdin:
            yield line.rstrip("\n")

    def close(self) -> None:
        """Nenhum recurso a liberar para stdin."""
        pass
