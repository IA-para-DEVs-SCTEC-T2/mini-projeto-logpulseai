"""Adaptador de leitura de arquivos de log locais (.log, .txt, .gz)."""

from __future__ import annotations

import gzip
import io
from collections.abc import Iterator
from pathlib import Path

from logpulse.sources.base import LogSource


class FileSource(LogSource):
    """Lê linhas de um arquivo de log local, com suporte a .gz."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._handle: io.TextIOBase | None = None

    def read_lines(self) -> Iterator[str]:
        """Lê e retorna linhas brutas do arquivo."""
        if self._path.suffix == ".gz":
            self._handle = gzip.open(self._path, "rt", encoding="utf-8")  # type: ignore[assignment]
        else:
            self._handle = open(self._path, encoding="utf-8")  # noqa: SIM115

        for line in self._handle:
            yield line.rstrip("\n")

    def close(self) -> None:
        """Fecha o arquivo aberto."""
        if self._handle:
            self._handle.close()
            self._handle = None
