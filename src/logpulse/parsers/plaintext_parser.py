"""Parser para logs em formato texto livre (Apache, Nginx, genérico)."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from logpulse.models import LogEntry, SeverityLevel
from logpulse.parsers.base import BaseParser

# Padrão genérico: [TIMESTAMP] LEVEL message
_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?"
    r"\s*\[?(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\]?"
    r"\s*(?P<message>.+)",
    re.IGNORECASE,
)

_LEVEL_MAP: dict[str, SeverityLevel] = {
    "debug": SeverityLevel.DEBUG,
    "info": SeverityLevel.INFO,
    "warning": SeverityLevel.WARNING,
    "warn": SeverityLevel.WARNING,
    "error": SeverityLevel.ERROR,
    "critical": SeverityLevel.CRITICAL,
    "fatal": SeverityLevel.CRITICAL,
}


class PlaintextParser(BaseParser):
    """Parseia linhas de log em formato texto livre."""

    def parse(self, line: str, source: str) -> LogEntry | None:
        """Transforma uma linha de texto em LogEntry. Retorna None se vazia."""
        line = line.strip()
        if not line:
            return None

        match = _PATTERN.match(line)
        if not match:
            return LogEntry(
                timestamp=datetime.now(tz=timezone.utc),
                level=SeverityLevel.INFO,
                message=line,
                source=source,
                raw=line,
                timestamp_inferred=True,
                level_inferred=True,
            )

        raw_ts = match.group("timestamp")
        timestamp, ts_inferred = _parse_timestamp(raw_ts)

        raw_level = (match.group("level") or "info").lower()
        level = _LEVEL_MAP.get(raw_level, SeverityLevel.INFO)

        message = match.group("message").strip()
        if not message:
            message = line

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            raw=line,
            timestamp_inferred=ts_inferred,
            level_inferred=False,
        )


def _parse_timestamp(raw: str | None) -> tuple[datetime, bool]:
    """Tenta converter string em datetime com timezone."""
    if raw:
        try:
            raw_normalized = raw.replace(" ", "T")
            dt = datetime.fromisoformat(raw_normalized)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt, False
        except ValueError:
            pass
    return datetime.now(tz=timezone.utc), True
