"""Testes unitários e de propriedade para os schemas Pydantic do LogPulse IA."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
    LogEntry,
    LogFileUpload,
    LogListParams,
    LogTemplate,
    LogTextUpload,
    SeverityLevel,
    Spike,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
_LATER = _NOW + timedelta(seconds=60)


def _make_hypothesis(**kwargs: object) -> Hypothesis:
    defaults: dict[str, object] = {
        "description": "Conexão com banco de dados falhou",
        "probability": "alta",
        "action": "Verificar string de conexão e disponibilidade do banco",
    }
    defaults.update(kwargs)
    return Hypothesis(**defaults)  # type: ignore[arg-type]


def _make_diagnosis(**kwargs: object) -> AIDiagnosis:
    defaults: dict[str, object] = {
        "summary": "Falha de conexão com banco de dados",
        "probable_cause": "Banco de dados indisponível",
        "hypotheses": [
            _make_hypothesis(description="Causa 1", probability="alta"),
            _make_hypothesis(description="Causa 2", probability="média"),
            _make_hypothesis(description="Causa 3", probability="baixa"),
        ],
    }
    defaults.update(kwargs)
    return AIDiagnosis(**defaults)  # type: ignore[arg-type]


def _make_analysis(**kwargs: object) -> AnalysisResult:
    defaults: dict[str, object] = {
        "total_entries": 10,
        "error_count": 2,
        "warning_count": 3,
    }
    defaults.update(kwargs)
    return AnalysisResult(**defaults)  # type: ignore[arg-type]


# ===========================================================================
# SeverityLevel
# ===========================================================================


class TestSeverityLevel:
    def test_all_values_exist(self) -> None:
        assert SeverityLevel.DEBUG == "DEBUG"
        assert SeverityLevel.INFO == "INFO"
        assert SeverityLevel.WARNING == "WARNING"
        assert SeverityLevel.ERROR == "ERROR"
        assert SeverityLevel.CRITICAL == "CRITICAL"

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            SeverityLevel("TRACE")  # type: ignore[call-arg]

    def test_is_string_enum(self) -> None:
        assert isinstance(SeverityLevel.INFO, str)


# ===========================================================================
# LogEntry
# ===========================================================================


class TestLogEntry:
    def test_minimal_valid_entry(self) -> None:
        entry = LogEntry(raw_content="ERROR: something went wrong")
        assert entry.raw_content == "ERROR: something went wrong"
        assert entry.severity == SeverityLevel.INFO
        assert entry.level_inferred is False
        assert entry.timestamp_inferred is False
        assert entry.template_id is None

    def test_auto_generates_uuid(self) -> None:
        e1 = LogEntry(raw_content="msg1")
        e2 = LogEntry(raw_content="msg2")
        assert e1.id != e2.id
        uuid.UUID(e1.id)  # não lança se for UUID válido

    def test_empty_raw_content_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogEntry(raw_content="")

    def test_inference_flags(self) -> None:
        entry = LogEntry(
            raw_content="some log",
            level_inferred=True,
            timestamp_inferred=True,
        )
        assert entry.level_inferred is True
        assert entry.timestamp_inferred is True

    def test_all_severity_levels_accepted(self) -> None:
        for level in SeverityLevel:
            entry = LogEntry(raw_content="msg", severity=level)
            assert entry.severity == level

    def test_whitespace_stripped(self) -> None:
        entry = LogEntry(raw_content="  hello world  ")
        assert entry.raw_content == "hello world"

    def test_template_id_optional(self) -> None:
        entry = LogEntry(raw_content="msg", template_id="tmpl-001")
        assert entry.template_id == "tmpl-001"

    def test_timestamp_optional(self) -> None:
        entry = LogEntry(raw_content="msg", timestamp=_NOW)
        assert entry.timestamp == _NOW


# ===========================================================================
# LogTemplate
# ===========================================================================


class TestLogTemplate:
    def test_valid_template(self) -> None:
        tmpl = LogTemplate(
            template_id="t1",
            pattern="Database timeout <*>",
            occurrences=5,
            sample_messages=["msg1", "msg2"],
        )
        assert tmpl.occurrences == 5
        assert len(tmpl.sample_messages) == 2

    def test_sample_messages_capped_at_5(self) -> None:
        msgs = [f"msg{i}" for i in range(10)]
        tmpl = LogTemplate(template_id="t1", pattern="p", sample_messages=msgs)
        assert len(tmpl.sample_messages) == 5

    def test_occurrences_non_negative(self) -> None:
        with pytest.raises(ValidationError):
            LogTemplate(template_id="t1", pattern="p", occurrences=-1)

    def test_default_occurrences_zero(self) -> None:
        tmpl = LogTemplate(template_id="t1", pattern="p")
        assert tmpl.occurrences == 0

    def test_empty_sample_messages_default(self) -> None:
        tmpl = LogTemplate(template_id="t1", pattern="p")
        assert tmpl.sample_messages == []


# ===========================================================================
# Spike
# ===========================================================================


class TestSpike:
    def test_valid_spike(self) -> None:
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        assert spike.error_count == 10

    def test_error_count_minimum_10(self) -> None:
        with pytest.raises(ValidationError):
            Spike(start_time=_NOW, end_time=_LATER, error_count=9)

    def test_end_time_must_be_after_start_time(self) -> None:
        with pytest.raises(ValidationError):
            Spike(start_time=_LATER, end_time=_NOW, error_count=10)

    def test_equal_times_raises(self) -> None:
        with pytest.raises(ValidationError):
            Spike(start_time=_NOW, end_time=_NOW, error_count=10)

    def test_template_ids_optional(self) -> None:
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=15, template_ids=["t1", "t2"])
        assert spike.template_ids == ["t1", "t2"]

    def test_template_ids_default_empty(self) -> None:
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        assert spike.template_ids == []


# ===========================================================================
# AnalysisResult
# ===========================================================================


class TestAnalysisResult:
    def test_default_values(self) -> None:
        result = AnalysisResult()
        assert result.total_entries == 0
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.spikes == []
        assert result.templates == []
        assert result.insufficient_data is False

    def test_negative_counters_raise(self) -> None:
        with pytest.raises(ValidationError):
            AnalysisResult(total_entries=-1)
        with pytest.raises(ValidationError):
            AnalysisResult(error_count=-1)
        with pytest.raises(ValidationError):
            AnalysisResult(warning_count=-1)

    def test_severity_distribution(self) -> None:
        dist = {SeverityLevel.ERROR: 5, SeverityLevel.INFO: 10}
        result = AnalysisResult(total_entries=15, severity_distribution=dist)
        assert result.severity_distribution[SeverityLevel.ERROR] == 5

    def test_insufficient_data_flag(self) -> None:
        result = AnalysisResult(total_entries=1, insufficient_data=True)
        assert result.insufficient_data is True

    def test_with_spikes(self) -> None:
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        result = AnalysisResult(total_entries=20, spikes=[spike])
        assert len(result.spikes) == 1


# ===========================================================================
# Hypothesis
# ===========================================================================


class TestHypothesis:
    def test_valid_hypothesis(self) -> None:
        h = _make_hypothesis()
        assert h.probability == "alta"
        assert h.related_line is None

    def test_probability_values(self) -> None:
        for prob in ("alta", "média", "baixa"):
            h = _make_hypothesis(probability=prob)
            assert h.probability == prob

    def test_probability_case_insensitive(self) -> None:
        h = _make_hypothesis(probability="ALTA")
        assert h.probability == "alta"

    def test_invalid_probability_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_hypothesis(probability="high")

    def test_empty_action_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_hypothesis(action="")

    def test_blank_action_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_hypothesis(action="   ")

    def test_related_line_optional(self) -> None:
        h = _make_hypothesis(related_line=42)
        assert h.related_line == 42

    def test_empty_description_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_hypothesis(description="")


# ===========================================================================
# AIDiagnosis
# ===========================================================================


class TestAIDiagnosis:
    def test_valid_diagnosis(self) -> None:
        diag = _make_diagnosis()
        assert len(diag.hypotheses) == 3

    def test_less_than_3_hypotheses_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnosis(
                hypotheses=[
                    _make_hypothesis(description="H1"),
                    _make_hypothesis(description="H2"),
                ]
            )

    def test_exactly_3_hypotheses_accepted(self) -> None:
        diag = _make_diagnosis()
        assert len(diag.hypotheses) == 3

    def test_more_than_3_hypotheses_accepted(self) -> None:
        diag = _make_diagnosis(
            hypotheses=[_make_hypothesis(description=f"H{i}") for i in range(5)]
        )
        assert len(diag.hypotheses) == 5

    def test_empty_summary_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnosis(summary="")

    def test_empty_probable_cause_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnosis(probable_cause="")

    def test_confidence_range(self) -> None:
        diag = _make_diagnosis(confidence=0.85)
        assert diag.confidence == 0.85

    def test_confidence_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            _make_diagnosis(confidence=1.5)
        with pytest.raises(ValidationError):
            _make_diagnosis(confidence=-0.1)

    def test_default_confidence_zero(self) -> None:
        diag = _make_diagnosis()
        assert diag.confidence == 0.0


# ===========================================================================
# LogFileUpload
# ===========================================================================


class TestLogFileUpload:
    def test_valid_log_file(self) -> None:
        upload = LogFileUpload(filename="app.log", content="some log content")
        assert upload.filename == "app.log"

    def test_valid_txt_file(self) -> None:
        upload = LogFileUpload(filename="errors.txt", content="error line")
        assert upload.filename == "errors.txt"

    def test_invalid_extension_raises(self) -> None:
        for ext in (".pdf", ".docx", ".csv", ".json", ".log.pdf"):
            with pytest.raises(ValidationError):
                LogFileUpload(filename=f"file{ext}", content="content")

    def test_case_insensitive_extension(self) -> None:
        upload = LogFileUpload(filename="APP.LOG", content="content")
        assert upload.filename == "APP.LOG"

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogFileUpload(filename="app.log", content="")

    def test_content_exceeding_50mb_raises(self) -> None:
        big_content = "x" * (50 * 1024 * 1024 + 1)
        with pytest.raises(ValidationError):
            LogFileUpload(filename="app.log", content=big_content)

    def test_content_at_50mb_limit_accepted(self) -> None:
        content = "x" * (50 * 1024 * 1024)
        upload = LogFileUpload(filename="app.log", content=content)
        assert len(upload.content) == 50 * 1024 * 1024


# ===========================================================================
# LogTextUpload
# ===========================================================================


class TestLogTextUpload:
    def test_valid_content(self) -> None:
        upload = LogTextUpload(content="ERROR: database connection failed")
        assert upload.content == "ERROR: database connection failed"

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogTextUpload(content="")

    def test_content_at_100k_limit_accepted(self) -> None:
        content = "x" * 100_000
        upload = LogTextUpload(content=content)
        assert len(upload.content) == 100_000

    def test_content_exceeding_100k_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogTextUpload(content="x" * 100_001)


# ===========================================================================
# LogListParams
# ===========================================================================


class TestLogListParams:
    def test_default_values(self) -> None:
        params = LogListParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_page_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogListParams(page=0)

    def test_page_size_101_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogListParams(page_size=101)

    def test_page_size_100_accepted(self) -> None:
        params = LogListParams(page_size=100)
        assert params.page_size == 100

    def test_page_size_1_accepted(self) -> None:
        params = LogListParams(page_size=1)
        assert params.page_size == 1

    def test_page_size_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            LogListParams(page_size=0)

    def test_custom_page(self) -> None:
        params = LogListParams(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50


# ===========================================================================
# LogAnalysisResponse
# ===========================================================================


class TestLogAnalysisResponse:
    def test_valid_response(self) -> None:
        response = LogAnalysisResponse(
            id=str(uuid.uuid4()),
            analysis=_make_analysis(),
            diagnosis=_make_diagnosis(),
            created_at=_NOW,
        )
        assert response.total_entries == 0
        assert response.summary == ""

    def test_all_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            LogAnalysisResponse(  # type: ignore[call-arg]
                analysis=_make_analysis(),
                diagnosis=_make_diagnosis(),
                created_at=_NOW,
            )


# ===========================================================================
# Property-Based Tests (Hypothesis library)
# ===========================================================================


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=50)
def test_log_entry_raw_content_preserved(raw: str) -> None:
    """Propriedade: raw_content não vazio é sempre aceito (após strip)."""
    stripped = raw.strip()
    if stripped:
        entry = LogEntry(raw_content=raw)
        assert entry.raw_content == stripped


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_log_list_params_valid_page(page: int) -> None:
    """Propriedade: qualquer page ≥ 1 é aceito."""
    params = LogListParams(page=page)
    assert params.page == page


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_log_list_params_valid_page_size(page_size: int) -> None:
    """Propriedade: qualquer page_size entre 1 e 100 é aceito."""
    params = LogListParams(page_size=page_size)
    assert params.page_size == page_size


@given(st.integers(max_value=0))
@settings(max_examples=30)
def test_log_list_params_invalid_page(page: int) -> None:
    """Propriedade: qualquer page ≤ 0 é rejeitado."""
    with pytest.raises(ValidationError):
        LogListParams(page=page)


@given(st.text(min_size=1, max_size=100_000))
@settings(max_examples=30)
def test_log_text_upload_valid_content(content: str) -> None:
    """Propriedade: qualquer conteúdo com 1–100k chars é aceito."""
    upload = LogTextUpload(content=content)
    assert len(upload.content) <= 100_000


@given(
    st.datetimes(timezones=st.just(timezone.utc)),
    st.timedeltas(min_value=timedelta(seconds=1), max_value=timedelta(hours=1)),
    st.integers(min_value=10, max_value=1000),
)
@settings(max_examples=30)
def test_spike_valid_time_range(
    start: datetime, delta: timedelta, count: int
) -> None:
    """Propriedade: Spike com end_time > start_time e error_count ≥ 10 é sempre válido."""
    end = start + delta
    spike = Spike(start_time=start, end_time=end, error_count=count)
    assert spike.end_time > spike.start_time
    assert spike.error_count >= 10


@given(st.sampled_from(["alta", "média", "baixa"]))
@settings(max_examples=20)
def test_hypothesis_valid_probabilities(prob: str) -> None:
    """Propriedade: todos os valores válidos de probability são aceitos."""
    h = _make_hypothesis(probability=prob)
    assert h.probability == prob
