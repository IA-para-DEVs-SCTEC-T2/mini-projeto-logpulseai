"""Parser para logs em formato JSON estruturado."""

from __future__ import annotations

from datetime import datetime, timezone

import orjson

from logpulse.models import LogEntry, SeverityLevel
from logpulse.parsers.base import BaseParser

_LEVEL_MAP: dict[str, SeverityLevel] = {
    "debug": SeverityLevel.DEBUG,
    "info": SeverityLevel.INFO,
    "warn": SeverityLevel.WARNING,
    "warning": SeverityLevel.WARNING,
    "error": SeverityLevel.ERROR,
    "critical": SeverityLevel.CRITICAL,
    "fatal": SeverityLevel.CRITICAL,
}


class JsonParser(BaseParser):
    """Parseia linhas de log no formato JSON (structured logging)."""

    def parse(self, line: str, source: str) -> LogEntry | None:
        """Transforma uma linha JSON em LogEntry. Retorna None se inválida."""
        line = line.strip()
        if not line or not line.startswith("{"):
            return None

        try:
            data: dict[str, object] = orjson.loads(line)
        except orjson.JSONDecodeError:
            return None

        message = str(data.get("message") or data.get("msg") or "")
        if not message:
            return None

        raw_level = str(data.get("level") or data.get("severity") or "info").lower()
        level = _LEVEL_MAP.get(raw_level, SeverityLevel.INFO)
        level_inferred = raw_level not in _LEVEL_MAP

        raw_ts = data.get("timestamp") or data.get("time") or data.get("ts")
        timestamp, ts_inferred = _parse_timestamp(raw_ts)

        extra = {k: v for k, v in data.items() if k not in {"message", "msg", "level", "severity", "timestamp", "time", "ts"}}

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            raw=line,
            timestamp_inferred=ts_inferred,
            level_inferred=level_inferred,
            extra=extra,
        )


def _parse_timestamp(raw: object) -> tuple[datetime, bool]:
    """Tenta converter um valor bruto em datetime com timezone."""
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt, False
        except ValueError:
            pass
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc), False
    return datetime.now(tz=timezone.utc), True
