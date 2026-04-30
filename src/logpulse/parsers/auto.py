"""Parser automático que detecta o formato da linha e delega ao parser correto."""

from __future__ import annotations

from logpulse.models import LogEntry
from logpulse.parsers.base import BaseParser
from logpulse.parsers.json_parser import JsonParser
from logpulse.parsers.plaintext_parser import PlaintextParser
from logpulse.parsers.syslog_parser import SyslogParser


class AutoParser(BaseParser):
    """Detecta automaticamente o formato do log e aplica o parser adequado."""

    def __init__(self) -> None:
        self._json = JsonParser()
        self._syslog = SyslogParser()
        self._plaintext = PlaintextParser()

    def parse(self, line: str, source: str) -> LogEntry | None:
        """Tenta cada parser em ordem e retorna o primeiro resultado válido."""
        return (
            self._json.parse(line, source)
            or self._syslog.parse(line, source)
            or self._plaintext.parse(line, source)
        )
