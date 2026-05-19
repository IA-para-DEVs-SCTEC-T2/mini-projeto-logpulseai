"""Normalização de severidade e inferência de timestamp para logs."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from src.models.schemas import SeverityLevel

# ---------------------------------------------------------------------------
# Mapeamento de aliases de severidade
# ---------------------------------------------------------------------------

_SEVERITY_ALIASES = {
    "trace": SeverityLevel.DEBUG,
    "debug": SeverityLevel.DEBUG,
    "info": SeverityLevel.INFO,
    "information": SeverityLevel.INFO,
    "warn": SeverityLevel.WARNING,
    "warning": SeverityLevel.WARNING,
    "err": SeverityLevel.ERROR,
    "error": SeverityLevel.ERROR,
    "fatal": SeverityLevel.CRITICAL,
    "critical": SeverityLevel.CRITICAL,
    "crit": SeverityLevel.CRITICAL,
    "emerg": SeverityLevel.CRITICAL,
    "alert": SeverityLevel.CRITICAL,
}

# ---------------------------------------------------------------------------
# Padrões de timestamp suportados
# ---------------------------------------------------------------------------

# ISO 8601 / RFC 3339: 2024-01-15T10:00:00Z ou 2024-01-15T10:00:00+00:00
_RE_ISO8601 = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")

# Syslog: Jan 15 10:00:00 ou Jan  5 10:00:00
_RE_SYSLOG_TS = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
)

# Formato com barra: 2024/01/15 10:00:00
_RE_SLASH_DATE = re.compile(r"\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}")

# Formato com traço sem T: 2024-01-15 10:00:00
_RE_DASH_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")

_SYSLOG_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def normalize_severity(raw_level: str | None) -> tuple[SeverityLevel, bool]:
    """Normaliza um nível de severidade bruto para SeverityLevel.

    Args:
        raw_level: String do nível de severidade (pode ser None).

    Returns:
        Tupla (SeverityLevel normalizado, inferred: bool).
        inferred=True quando o nível foi inferido por ausência ou valor inválido.
    """
    if not raw_level:
        return SeverityLevel.INFO, True

    normalized = raw_level.strip().lower()
    level = _SEVERITY_ALIASES.get(normalized)
    if level is not None:
        return level, False

    # Tenta match parcial (ex: "[ERROR]" → "error")
    for alias, sev in _SEVERITY_ALIASES.items():
        if alias in normalized:
            return sev, False

    return SeverityLevel.INFO, True


def parse_timestamp(raw_ts: str | None) -> tuple[datetime | None, bool]:
    """Tenta parsear um timestamp bruto em datetime com timezone.

    Args:
        raw_ts: String do timestamp (pode ser None).

    Returns:
        Tupla (datetime ou None, inferred: bool).
        inferred=True quando o timestamp foi inferido (ausente ou inválido).
    """
    if not raw_ts:
        return datetime.now(UTC), True

    ts = raw_ts.strip()

    # ISO 8601 com Z
    if ts.endswith("Z"):
        try:
            dt = datetime.fromisoformat(ts[:-1] + "+00:00")
            return dt, False
        except ValueError:
            pass

    # ISO 8601 / RFC 3339 completo
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt, False
    except ValueError:
        pass

    # Formato com barra: 2024/01/15 10:00:00
    m = _RE_SLASH_DATE.match(ts)
    if m:
        try:
            dt = datetime.strptime(m.group(), "%Y/%m/%d %H:%M:%S")
            return dt.replace(tzinfo=UTC), False
        except ValueError:
            pass

    # Syslog: Jan 15 10:00:00
    m2 = _RE_SYSLOG_TS.match(ts)
    if m2:
        try:
            parts = m2.group().split()
            month = _SYSLOG_MONTHS.get(parts[0], 1)
            day = int(parts[1])
            time_parts = parts[2].split(":")
            year = datetime.now(UTC).year
            dt = datetime(
                year,
                month,
                day,
                int(time_parts[0]),
                int(time_parts[1]),
                int(time_parts[2]),
                tzinfo=UTC,
            )
            return dt, False
        except (ValueError, IndexError):
            pass

    # Fallback: timestamp inválido → usa agora
    return datetime.now(UTC), True


def extract_timestamp_from_line(line: str) -> tuple[datetime | None, bool, str]:
    """Tenta extrair timestamp de uma linha de log em texto livre.

    Args:
        line: Linha bruta de log.

    Returns:
        Tupla (datetime ou None, inferred: bool, linha sem o timestamp).
    """
    for pattern in (_RE_ISO8601, _RE_SLASH_DATE, _RE_DASH_DATE, _RE_SYSLOG_TS):
        m = pattern.search(line)
        if m:
            ts_str = m.group()
            dt, inferred = parse_timestamp(ts_str)
            remaining = line[: m.start()].strip() + " " + line[m.end() :].strip()
            return dt, inferred, remaining.strip()

    return datetime.now(UTC), True, line
