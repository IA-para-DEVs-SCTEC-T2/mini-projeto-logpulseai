"""Testes unitários e de integração para o Drain3LogParser."""

from __future__ import annotations

import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.schemas import SeverityLevel
from src.parsers.base import LogParser
from src.parsers.drain3_parser import Drain3LogParser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def parser() -> Drain3LogParser:
    """Instância limpa do Drain3LogParser para cada teste."""
    return Drain3LogParser()


# ===========================================================================
# Interface abstrata
# ===========================================================================


class TestLogParserInterface:
    def test_cannot_instantiate_abstract(self) -> None:
        """LogParser não pode ser instanciado diretamente."""
        with pytest.raises(TypeError):
            LogParser()  # type: ignore[abstract]

    def test_drain3_is_subclass(self) -> None:
        assert issubclass(Drain3LogParser, LogParser)

    def test_drain3_implements_parse(self) -> None:
        p = Drain3LogParser()
        assert callable(p.parse)

    def test_drain3_implements_get_templates(self) -> None:
        p = Drain3LogParser()
        assert callable(p.get_templates)


# ===========================================================================
# Formato JSON
# ===========================================================================


class TestJsonFormat:
    def test_valid_json_entry(self, parser: Drain3LogParser) -> None:
        line = json.dumps({
            "timestamp": "2024-01-15T10:00:00Z",
            "level": "ERROR",
            "message": "Database connection failed",
        })
        entries = parser.parse(line)
        assert len(entries) == 1
        assert entries[0].severity == SeverityLevel.ERROR
        assert entries[0].message == "Database connection failed"
        assert entries[0].level_inferred is False
        assert entries[0].timestamp_inferred is False

    def test_json_with_warn_alias(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"timestamp": "2024-01-15T10:00:00Z", "level": "WARN", "message": "Low memory"})
        entries = parser.parse(line)
        assert entries[0].severity == SeverityLevel.WARNING
        assert entries[0].level_inferred is False

    def test_json_with_fatal_alias(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"level": "FATAL", "message": "System crash"})
        entries = parser.parse(line)
        assert entries[0].severity == SeverityLevel.CRITICAL

    def test_json_with_trace_alias(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"level": "TRACE", "message": "Entering function"})
        entries = parser.parse(line)
        assert entries[0].severity == SeverityLevel.DEBUG

    def test_json_missing_level_inferred(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"timestamp": "2024-01-15T10:00:00Z", "message": "No level here"})
        entries = parser.parse(line)
        assert entries[0].level_inferred is True
        assert entries[0].severity == SeverityLevel.INFO

    def test_json_missing_timestamp_inferred(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"level": "INFO", "message": "No timestamp"})
        entries = parser.parse(line)
        assert entries[0].timestamp_inferred is True

    def test_json_alternative_keys(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"ts": "2024-01-15T10:00:00Z", "lvl": "ERROR", "msg": "Alt keys"})
        entries = parser.parse(line)
        assert len(entries) == 1
        assert entries[0].message == "Alt keys"

    def test_json_raw_content_preserved(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"level": "INFO", "message": "test"})
        entries = parser.parse(line)
        assert entries[0].raw_content == line

    def test_json_has_template_id(self, parser: Drain3LogParser) -> None:
        line = json.dumps({"level": "INFO", "message": "User 123 logged in"})
        entries = parser.parse(line)
        assert entries[0].template_id is not None


# ===========================================================================
# Formato Syslog RFC 3164
# ===========================================================================


class TestSyslogFormat:
    def test_valid_syslog_entry(self, parser: Drain3LogParser) -> None:
        line = "Jan 15 10:00:00 myhost myapp[1234]: ERROR: connection refused"
        entries = parser.parse(line)
        assert len(entries) == 1
        assert entries[0].timestamp_inferred is False
        assert entries[0].timestamp is not None
        assert entries[0].timestamp.month == 1
        assert entries[0].timestamp.day == 15

    def test_syslog_extracts_error_level(self, parser: Drain3LogParser) -> None:
        line = "Jan 15 10:00:00 host app: ERROR database timeout"
        entries = parser.parse(line)
        assert entries[0].severity == SeverityLevel.ERROR
        assert entries[0].level_inferred is False

    def test_syslog_extracts_warning_level(self, parser: Drain3LogParser) -> None:
        line = "Feb  5 08:30:00 host app: WARNING high memory usage"
        entries = parser.parse(line)
        assert entries[0].severity == SeverityLevel.WARNING

    def test_syslog_no_level_inferred(self, parser: Drain3LogParser) -> None:
        line = "Mar 10 12:00:00 host app: just a plain message"
        entries = parser.parse(line)
        assert entries[0].level_inferred is True

    def test_syslog_raw_content_preserved(self, parser: Drain3LogParser) -> None:
        line = "Jan 15 10:00:00 host app: test message"
        entries = parser.parse(line)
        assert entries[0].raw_content == line


# ===========================================================================
# Formato texto livre (plaintext)
# ===========================================================================


class TestPlaintextFormat:
    def test_simple_error_line(self, parser: Drain3LogParser) -> None:
        line = "ERROR: something went wrong"
        entries = parser.parse(line)
        assert len(entries) == 1
        assert entries[0].severity == SeverityLevel.ERROR
        assert entries[0].level_inferred is False

    def test_line_with_iso_timestamp(self, parser: Drain3LogParser) -> None:
        line = "2024-01-15T10:00:00Z ERROR database connection failed"
        entries = parser.parse(line)
        assert entries[0].timestamp_inferred is False
        assert entries[0].severity == SeverityLevel.ERROR

    def test_line_without_timestamp_inferred(self, parser: Drain3LogParser) -> None:
        line = "WARNING: disk space low"
        entries = parser.parse(line)
        assert entries[0].timestamp_inferred is True

    def test_line_without_level_inferred(self, parser: Drain3LogParser) -> None:
        line = "2024-01-15T10:00:00Z just a plain message"
        entries = parser.parse(line)
        assert entries[0].level_inferred is True
        assert entries[0].severity == SeverityLevel.INFO

    def test_empty_lines_skipped(self, parser: Drain3LogParser) -> None:
        content = "\n\n  \nERROR: test\n\n"
        entries = parser.parse(content)
        assert len(entries) == 1

    def test_malformed_line_does_not_crash(self, parser: Drain3LogParser) -> None:
        content = "valid line ERROR: ok\n\x00\x01\x02\nERROR: another valid"
        # Não deve lançar exceção
        entries = parser.parse(content)
        assert len(entries) >= 1

    def test_raw_content_preserved(self, parser: Drain3LogParser) -> None:
        line = "ERROR: test message"
        entries = parser.parse(line)
        assert entries[0].raw_content == line


# ===========================================================================
# Normalização de severidade
# ===========================================================================


class TestSeverityNormalization:
    def test_warn_to_warning(self, parser: Drain3LogParser) -> None:
        entries = parser.parse(json.dumps({"level": "WARN", "message": "test"}))
        assert entries[0].severity == SeverityLevel.WARNING

    def test_err_to_error(self, parser: Drain3LogParser) -> None:
        entries = parser.parse(json.dumps({"level": "ERR", "message": "test"}))
        assert entries[0].severity == SeverityLevel.ERROR

    def test_fatal_to_critical(self, parser: Drain3LogParser) -> None:
        entries = parser.parse(json.dumps({"level": "FATAL", "message": "test"}))
        assert entries[0].severity == SeverityLevel.CRITICAL

    def test_trace_to_debug(self, parser: Drain3LogParser) -> None:
        entries = parser.parse(json.dumps({"level": "TRACE", "message": "test"}))
        assert entries[0].severity == SeverityLevel.DEBUG

    def test_case_insensitive_in_json(self, parser: Drain3LogParser) -> None:
        for variant in ("warn", "WARN", "Warn"):
            p = Drain3LogParser()
            entries = p.parse(json.dumps({"level": variant, "message": "test"}))
            assert entries[0].severity == SeverityLevel.WARNING


# ===========================================================================
# Extração de templates (Drain3)
# ===========================================================================


class TestTemplateExtraction:
    def test_templates_empty_initially(self, parser: Drain3LogParser) -> None:
        assert parser.get_templates() == []

    def test_template_created_after_parse(self, parser: Drain3LogParser) -> None:
        parser.parse("ERROR: database connection failed")
        templates = parser.get_templates()
        assert len(templates) >= 1

    def test_similar_messages_same_template(self, parser: Drain3LogParser) -> None:
        content = "\n".join([
            "ERROR: user 1 login failed",
            "ERROR: user 2 login failed",
            "ERROR: user 3 login failed",
            "ERROR: user 4 login failed",
            "ERROR: user 5 login failed",
        ])
        entries = parser.parse(content)
        template_ids = {e.template_id for e in entries}
        # Mensagens similares devem ter o mesmo template
        assert len(template_ids) <= 2  # Drain3 pode criar 1 ou 2 clusters

    def test_template_has_occurrences(self, parser: Drain3LogParser) -> None:
        for i in range(3):
            parser.parse(f"ERROR: connection timeout after {i}s")
        templates = parser.get_templates()
        total = sum(t.occurrences for t in templates)
        assert total == 3

    def test_sample_messages_max_5(self, parser: Drain3LogParser) -> None:
        for i in range(10):
            parser.parse(f"INFO: request {i} processed")
        templates = parser.get_templates()
        for t in templates:
            assert len(t.sample_messages) <= 5

    def test_template_has_pattern(self, parser: Drain3LogParser) -> None:
        parser.parse("ERROR: user 42 not found")
        parser.parse("ERROR: user 99 not found")
        templates = parser.get_templates()
        assert any(t.pattern for t in templates)

    def test_entries_have_template_id(self, parser: Drain3LogParser) -> None:
        entries = parser.parse("ERROR: test message")
        assert entries[0].template_id is not None
        assert entries[0].template_id != ""


# ===========================================================================
# Processamento em lote (1000 linhas)
# ===========================================================================


class TestBatchProcessing:
    def test_1000_lines_no_error(self, parser: Drain3LogParser) -> None:
        """Parser processa 1000 linhas sem erros (RNF-03)."""
        lines = []
        for i in range(1000):
            level = ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"][i % 5]
            lines.append(f"2024-01-15T10:00:00Z {level}: message number {i}")
        content = "\n".join(lines)
        entries = parser.parse(content)
        assert len(entries) == 1000

    def test_mixed_formats_in_batch(self, parser: Drain3LogParser) -> None:
        """Parser lida com múltiplos formatos na mesma entrada."""
        lines = [
            json.dumps({"level": "ERROR", "message": "json error"}),
            "Jan 15 10:00:00 host app: syslog message",
            "ERROR: plaintext error",
            "2024-01-15T10:00:00Z INFO: iso timestamp line",
        ]
        entries = parser.parse("\n".join(lines))
        assert len(entries) == 4

    def test_all_entries_have_uuid(self, parser: Drain3LogParser) -> None:
        content = "\n".join([f"ERROR: msg {i}" for i in range(10)])
        entries = parser.parse(content)
        ids = {e.id for e in entries}
        assert len(ids) == 10  # todos únicos

    def test_all_entries_have_timezone(self, parser: Drain3LogParser) -> None:
        content = "\n".join([f"ERROR: msg {i}" for i in range(5)])
        entries = parser.parse(content)
        for e in entries:
            if e.timestamp:
                assert e.timestamp.tzinfo is not None


# ===========================================================================
# Property-based tests
# ===========================================================================


@given(st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != ""))
@settings(max_examples=50)
def test_parse_never_raises(text: str) -> None:
    """Propriedade: parse() nunca lança exceção para qualquer entrada."""
    parser = Drain3LogParser()
    result = parser.parse(text)
    assert isinstance(result, list)


@given(st.integers(min_value=1, max_value=50))
@settings(max_examples=20)
def test_sample_messages_always_bounded(n: int) -> None:
    """Propriedade: sample_messages nunca excede 5 independente do volume."""
    parser = Drain3LogParser()
    for i in range(n):
        parser.parse(f"ERROR: repeated message pattern {i}")
    for t in parser.get_templates():
        assert len(t.sample_messages) <= 5
