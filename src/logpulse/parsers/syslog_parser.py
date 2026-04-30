"""Parser para logs no formato Syslog (RFC 3164 / RFC 5424)."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from logpulse.models import LogEntry, SeverityLevel
from logpulse.parsers.base import BaseParser

# RFC 3164: <PRI>MMM DD HH:MM:SS hostname tag: message
_RFC3164 = re.compile(
    r"<(?P<pri>\d+)>(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})"
    r"\s+(?P<host>\S+)\s+(?P<tag>\S+?):\s*(?P<message>.*)"
)

# Mapeamento de severidade syslog (0=EMERG ... 7=DEBUG)
_SYSLOG_SEVERITY: dict[int, SeverityLevel] = {
    0: SeverityLevel.CRITICAL,
    1: SeverityLevel.CRITICAL,
    2: SeverityLevel.CRITICAL,
    3: SeverityLevel.ERROR,
    4: SeverityLevel.WARNING,
    5: SeverityLevel.INFO,
    6: SeverityLevel.INFO,
    7: SeverityLevel.DEBUG,
}


class SyslogParser(BaseParser):
    """Parseia linhas de log no formato Syslog RFC 3164."""

    def parse(self, line: str, source: str) -> LogEntry | None:
        """Transforma uma linha syslog em LogEntry. Retorna None se não reconhecida."""
        line = line.strip()
        if not line:
            return None

        match = _RFC3164.match(line)
        if not match:
            return None

        pri = int(match.group("pri"))
        severity = pri % 8
        level = _SYSLOG_SEVERITY.get(severity, SeverityLevel.INFO)

        message = match.group("message").strip() or line
        extra = {"host": match.group("host"), "tag": match.group("tag")}

        return LogEntry(
            timestamp=datetime.now(tz=timezone.utc),
            level=level,
            message=message,
            source=source,
            raw=line,
            timestamp_inferred=True,
            extra=extra,
        )
