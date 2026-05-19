"""Testes unitários para o módulo de normalização de severidade e timestamp."""

from __future__ import annotations

from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.schemas import SeverityLevel
from src.parsers.normalizer import (
    extract_timestamp_from_line,
    normalize_severity,
    parse_timestamp,
)

# ===========================================================================
# normalize_severity
# ===========================================================================


class TestNormalizeSeverity:
    def test_none_returns_info_inferred(self) -> None:
        level, inferred = normalize_severity(None)
        assert level == SeverityLevel.INFO
        assert inferred is True

    def test_empty_string_returns_info_inferred(self) -> None:
        level, inferred = normalize_severity("")
        assert level == SeverityLevel.INFO
        assert inferred is True

    def test_warn_alias(self) -> None:
        level, inferred = normalize_severity("WARN")
        assert level == SeverityLevel.WARNING
        assert inferred is False

    def test_err_alias(self) -> None:
        level, inferred = normalize_severity("ERR")
        assert level == SeverityLevel.ERROR
        assert inferred is False

    def test_fatal_alias(self) -> None:
        level, inferred = normalize_severity("FATAL")
        assert level == SeverityLevel.CRITICAL
        assert inferred is False

    def test_trace_alias(self) -> None:
        level, inferred = normalize_severity("TRACE")
        assert level == SeverityLevel.DEBUG
        assert inferred is False

    def test_case_insensitive_warn(self) -> None:
        for variant in ("warn", "WARN", "Warn", "wArN"):
            level, inferred = normalize_severity(variant)
            assert level == SeverityLevel.WARNING
            assert inferred is False

    def test_case_insensitive_error(self) -> None:
        for variant in ("error", "ERROR", "Error"):
            level, inferred = normalize_severity(variant)
            assert level == SeverityLevel.ERROR
            assert inferred is False

    def test_debug_direct(self) -> None:
        level, inferred = normalize_severity("DEBUG")
        assert level == SeverityLevel.DEBUG
        assert inferred is False

    def test_info_direct(self) -> None:
        level, inferred = normalize_severity("INFO")
        assert level == SeverityLevel.INFO
        assert inferred is False

    def test_critical_direct(self) -> None:
        level, inferred = normalize_severity("CRITICAL")
        assert level == SeverityLevel.CRITICAL
        assert inferred is False

    def test_unknown_returns_info_inferred(self) -> None:
        level, inferred = normalize_severity("VERBOSE")
        assert level == SeverityLevel.INFO
        assert inferred is True

    def test_crit_alias(self) -> None:
        level, inferred = normalize_severity("CRIT")
        assert level == SeverityLevel.CRITICAL
        assert inferred is False

    def test_emerg_alias(self) -> None:
        level, inferred = normalize_severity("EMERG")
        assert level == SeverityLevel.CRITICAL
        assert inferred is False


# ===========================================================================
# parse_timestamp
# ===========================================================================


class TestParseTimestamp:
    def test_none_returns_now_inferred(self) -> None:
        dt, inferred = parse_timestamp(None)
        assert inferred is True
        assert dt is not None
        assert dt.tzinfo is not None

    def test_iso8601_with_z(self) -> None:
        dt, inferred = parse_timestamp("2024-01-15T10:00:00Z")
        assert inferred is False
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.tzinfo is not None

    def test_iso8601_with_offset(self) -> None:
        dt, inferred = parse_timestamp("2024-01-15T10:00:00+00:00")
        assert inferred is False
        assert dt is not None
        assert dt.tzinfo is not None

    def test_rfc3339_space_separator(self) -> None:
        dt, inferred = parse_timestamp("2024-01-15 10:00:00")
        assert inferred is False
        assert dt is not None
        assert dt.year == 2024

    def test_slash_format(self) -> None:
        dt, inferred = parse_timestamp("2024/01/15 10:00:00")
        assert inferred is False
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1

    def test_syslog_format(self) -> None:
        dt, inferred = parse_timestamp("Jan 15 10:00:00")
        assert inferred is False
        assert dt is not None
        assert dt.month == 1
        assert dt.day == 15

    def test_invalid_returns_now_inferred(self) -> None:
        dt, inferred = parse_timestamp("not-a-timestamp")
        assert inferred is True
        assert dt is not None

    def test_result_always_has_timezone(self) -> None:
        for ts in ("2024-01-15T10:00:00Z", "Jan 15 10:00:00", None):
            dt, _ = parse_timestamp(ts)
            assert dt is not None
            assert dt.tzinfo is not None


# ===========================================================================
# extract_timestamp_from_line
# ===========================================================================


class TestExtractTimestampFromLine:
    def test_iso8601_in_line(self) -> None:
        line = "2024-01-15T10:00:00Z ERROR database connection failed"
        dt, inferred, remaining = extract_timestamp_from_line(line)
        assert inferred is False
        assert dt is not None
        assert "database connection failed" in remaining

    def test_no_timestamp_in_line(self) -> None:
        line = "ERROR: something went wrong"
        dt, inferred, remaining = extract_timestamp_from_line(line)
        assert inferred is True
        assert remaining == line

    def test_syslog_timestamp_in_line(self) -> None:
        line = "Jan 15 10:00:00 host app: message here"
        dt, inferred, remaining = extract_timestamp_from_line(line)
        assert inferred is False
        assert dt is not None


# ===========================================================================
# Property-based tests
# ===========================================================================


@given(st.sampled_from(["warn", "WARN", "Warn", "err", "ERR", "fatal", "FATAL", "trace", "TRACE"]))
@settings(max_examples=20)
def test_all_aliases_never_inferred(alias: str) -> None:
    """Propriedade: aliases conhecidos nunca são marcados como inferidos."""
    _, inferred = normalize_severity(alias)
    assert inferred is False


@given(st.datetimes(timezones=st.just(UTC)))
@settings(max_examples=30)
def test_parse_timestamp_iso_roundtrip(dt: datetime) -> None:
    """Propriedade: datetime → ISO string → parse_timestamp preserva data."""
    iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    parsed, inferred = parse_timestamp(iso)
    assert inferred is False
    assert parsed is not None
    assert parsed.year == dt.year
    assert parsed.month == dt.month
    assert parsed.day == dt.day
