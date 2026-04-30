"""Testes para o Analyzer."""

from datetime import datetime, timedelta, timezone

import pytest

from logpulse.analyzer.engine import Analyzer
from logpulse.models import LogEntry, SeverityLevel


def make_entry(level: SeverityLevel, message: str = "msg", offset_seconds: int = 0) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 15, 10, 0, offset_seconds, tzinfo=timezone.utc),
        level=level,
        message=message,
        source="test",
    )


def test_analyze_empty_returns_zeros() -> None:
    result = Analyzer().analyze([])
    assert result.total_entries == 0
    assert result.error_count == 0


def test_analyze_counts_errors_and_warnings() -> None:
    entries = [
        make_entry(SeverityLevel.ERROR),
        make_entry(SeverityLevel.CRITICAL),
        make_entry(SeverityLevel.WARNING),
        make_entry(SeverityLevel.INFO),
    ]
    result = Analyzer().analyze(entries)
    assert result.total_entries == 4
    assert result.error_count == 2
    assert result.warning_count == 1


def test_analyze_detects_repeated_anomaly() -> None:
    entries = [make_entry(SeverityLevel.ERROR, "DB timeout") for _ in range(5)]
    result = Analyzer().analyze(entries)
    assert any("DB timeout" in a for a in result.anomalies)
