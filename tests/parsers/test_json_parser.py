"""Testes para o JsonParser."""

from datetime import timezone

import pytest

from logpulse.models import SeverityLevel
from logpulse.parsers.json_parser import JsonParser


@pytest.fixture
def parser() -> JsonParser:
    return JsonParser()


def test_parse_valid_json(parser: JsonParser) -> None:
    line = '{"timestamp": "2024-01-15T10:00:00+00:00", "level": "error", "message": "DB failed"}'
    entry = parser.parse(line, "test")
    assert entry is not None
    assert entry.level == SeverityLevel.ERROR
    assert entry.message == "DB failed"
    assert entry.timestamp.tzinfo is not None


def test_parse_invalid_json_returns_none(parser: JsonParser) -> None:
    assert parser.parse("not json", "test") is None


def test_parse_empty_line_returns_none(parser: JsonParser) -> None:
    assert parser.parse("", "test") is None


def test_parse_infers_timestamp_when_missing(parser: JsonParser) -> None:
    line = '{"message": "hello", "level": "info"}'
    entry = parser.parse(line, "test")
    assert entry is not None
    assert entry.timestamp_inferred is True
    assert entry.timestamp.tzinfo == timezone.utc


def test_parse_extra_fields(parser: JsonParser) -> None:
    line = '{"message": "ok", "level": "info", "request_id": "abc123"}'
    entry = parser.parse(line, "test")
    assert entry is not None
    assert entry.extra.get("request_id") == "abc123"
