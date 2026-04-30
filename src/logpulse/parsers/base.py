"""Interface base para parsers de log."""

from __future__ import annotations

from abc import ABC, abstractmethod

from logpulse.models import LogEntry


class BaseParser(ABC):
    """Interface abstrata para transformação de texto bruto em LogEntry."""

    @abstractmethod
    def parse(self, line: str, source: str) -> LogEntry | None:
        """
        Transforma uma linha de texto bruto em um LogEntry estruturado.

        Retorna None se a linha não puder ser parseada.
        """
        ...
