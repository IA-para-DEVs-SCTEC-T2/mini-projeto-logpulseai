"""Testes de propriedade (property-based testing) para schemas Pydantic.

Usa Hypothesis para gerar inputs aleatórios e validar propriedades universais
dos schemas Pydantic.
"""

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogEntry,
    LogFileUpload,
    LogListParams,
    LogTemplate,
    LogTextUpload,
    SeverityLevel,
    Spike,
)


# ============================================================================
# Estratégias customizadas
# ============================================================================


@st.composite
def severity_level_strategy(draw: st.DrawFn) -> SeverityLevel:
    """Gera um SeverityLevel válido."""
    return draw(st.sampled_from(list(SeverityLevel)))


@st.composite
def datetime_strategy(draw: st.DrawFn) -> datetime:
    """Gera um datetime com timezone UTC."""
    dt = draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    return dt.replace(tzinfo=timezone.utc)


@st.composite
def hypothesis_strategy(draw: st.DrawFn) -> Hypothesis:
    """Gera uma Hypothesis válida."""
    # Garante que action não seja apenas espaços em branco
    action = draw(st.text(min_size=1, max_size=200))
    while not action.strip():
        action = draw(st.text(min_size=1, max_size=200))
    
    return Hypothesis(
        description=draw(st.text(min_size=1, max_size=200)),
        probability=draw(st.sampled_from(["alta", "média", "baixa"])),
        action=action,
        related_line=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10000))),
    )


# ============================================================================
# Testes de propriedade para LogEntry
# ============================================================================


class TestLogEntryProperties:
    """Testes de propriedade para LogEntry."""

    @given(st.text(min_size=1, max_size=1000))
    def test_log_entry_accepts_any_non_empty_raw_content(self, raw_content: str) -> None:
        """Propriedade: LogEntry aceita qualquer raw_content não vazio após strip."""
        # LogEntry faz strip do conteúdo, então strings que viram vazias após strip são rejeitadas
        if not raw_content.strip():
            with pytest.raises(ValidationError):
                LogEntry(raw_content=raw_content)
        else:
            entry = LogEntry(raw_content=raw_content)
            assert entry.raw_content == raw_content.strip()

    @given(severity_level_strategy())
    def test_log_entry_accepts_all_severity_levels(self, severity: SeverityLevel) -> None:
        """Propriedade: LogEntry aceita todos os SeverityLevel válidos."""
        entry = LogEntry(raw_content="test", severity=severity)
        assert entry.severity == severity

    @given(st.booleans(), st.booleans())
    def test_log_entry_inference_flags_are_preserved(
        self, level_inferred: bool, timestamp_inferred: bool
    ) -> None:
        """Propriedade: Flags de inferência são preservadas."""
        entry = LogEntry(
            raw_content="test",
            level_inferred=level_inferred,
            timestamp_inferred=timestamp_inferred,
        )
        assert entry.level_inferred == level_inferred
        assert entry.timestamp_inferred == timestamp_inferred


# ============================================================================
# Testes de propriedade para LogTemplate
# ============================================================================


class TestLogTemplateProperties:
    """Testes de propriedade para LogTemplate."""

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=20))
    def test_log_template_always_limits_samples_to_5(self, samples: list[str]) -> None:
        """Propriedade: sample_messages sempre limitado a 5 itens."""
        template = LogTemplate(
            template_id="test-id",
            pattern="test pattern",
            sample_messages=samples,
        )
        assert len(template.sample_messages) <= 5

    @given(st.integers(min_value=0, max_value=10000))
    def test_log_template_accepts_non_negative_occurrences(self, occurrences: int) -> None:
        """Propriedade: occurrences aceita qualquer inteiro não-negativo."""
        template = LogTemplate(
            template_id="test-id",
            pattern="test pattern",
            occurrences=occurrences,
        )
        assert template.occurrences == occurrences


# ============================================================================
# Testes de propriedade para Spike
# ============================================================================


class TestSpikeProperties:
    """Testes de propriedade para Spike."""

    @given(
        datetime_strategy(),
        st.integers(min_value=1, max_value=3600),  # segundos de diferença
        st.integers(min_value=10, max_value=1000),
    )
    def test_spike_accepts_valid_time_ranges(
        self, start: datetime, seconds_diff: int, error_count: int
    ) -> None:
        """Propriedade: Spike aceita qualquer end_time > start_time."""
        end = start + timedelta(seconds=seconds_diff)
        spike = Spike(start_time=start, end_time=end, error_count=error_count)
        assert spike.start_time == start
        assert spike.end_time == end
        assert spike.error_count == error_count

    @given(datetime_strategy(), st.integers(min_value=10, max_value=1000))
    def test_spike_rejects_end_time_before_start_time(
        self, start: datetime, error_count: int
    ) -> None:
        """Propriedade: Spike sempre rejeita end_time <= start_time."""
        end = start - timedelta(seconds=1)
        with pytest.raises(ValidationError):
            Spike(start_time=start, end_time=end, error_count=error_count)


# ============================================================================
# Testes de propriedade para Hypothesis
# ============================================================================


class TestHypothesisProperties:
    """Testes de propriedade para Hypothesis."""

    @given(st.sampled_from(["alta", "média", "baixa", "ALTA", "Média", "BAIXA"]))
    def test_hypothesis_normalizes_probability(self, probability: str) -> None:
        """Propriedade: probability sempre normalizado para lowercase."""
        hyp = Hypothesis(description="test", probability=probability, action="test")
        assert hyp.probability in ["alta", "média", "baixa"]
        assert hyp.probability == hyp.probability.lower()

    @given(st.text(min_size=1, max_size=200))
    def test_hypothesis_accepts_any_non_empty_action(self, action: str) -> None:
        """Propriedade: action aceita qualquer texto não vazio."""
        if action.strip():  # Apenas se não for apenas espaços
            hyp = Hypothesis(description="test", probability="alta", action=action)
            assert hyp.action == action


# ============================================================================
# Testes de propriedade para AIDiagnosis
# ============================================================================


class TestAIDiagnosisProperties:
    """Testes de propriedade para AIDiagnosis."""

    @given(st.lists(hypothesis_strategy(), min_size=3, max_size=10))
    def test_ai_diagnosis_accepts_3_or_more_hypotheses(
        self, hypotheses: list[Hypothesis]
    ) -> None:
        """Propriedade: AIDiagnosis aceita qualquer lista com >= 3 hypotheses."""
        diagnosis = AIDiagnosis(
            summary="test summary",
            probable_cause="test cause",
            hypotheses=hypotheses,
        )
        assert len(diagnosis.hypotheses) >= 3

    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_ai_diagnosis_accepts_confidence_in_range(self, confidence: float) -> None:
        """Propriedade: confidence aceita qualquer valor entre 0.0 e 1.0."""
        diagnosis = AIDiagnosis(
            summary="test",
            probable_cause="test",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="A1"),
                Hypothesis(description="H2", probability="média", action="A2"),
                Hypothesis(description="H3", probability="baixa", action="A3"),
            ],
            confidence=confidence,
        )
        assert 0.0 <= diagnosis.confidence <= 1.0


# ============================================================================
# Testes de propriedade para LogFileUpload
# ============================================================================


class TestLogFileUploadProperties:
    """Testes de propriedade para LogFileUpload."""

    @given(st.sampled_from(["test.log", "app.txt", "error.LOG", "debug.TXT"]))
    def test_log_file_upload_accepts_valid_extensions(self, filename: str) -> None:
        """Propriedade: LogFileUpload aceita .log e .txt (case-insensitive)."""
        upload = LogFileUpload(filename=filename, content="test content")
        assert upload.filename == filename

    @given(st.text(min_size=1, max_size=1000))
    def test_log_file_upload_preserves_content(self, content: str) -> None:
        """Propriedade: content é preservado sem modificação."""
        upload = LogFileUpload(filename="test.log", content=content)
        assert upload.content == content


# ============================================================================
# Testes de propriedade para LogTextUpload
# ============================================================================


class TestLogTextUploadProperties:
    """Testes de propriedade para LogTextUpload."""

    @given(st.text(min_size=1, max_size=100_000))
    def test_log_text_upload_accepts_content_up_to_100k(self, content: str) -> None:
        """Propriedade: LogTextUpload aceita qualquer texto até 100k chars."""
        upload = LogTextUpload(content=content)
        assert upload.content == content
        assert len(upload.content) <= 100_000


# ============================================================================
# Testes de propriedade para LogListParams
# ============================================================================


class TestLogListParamsProperties:
    """Testes de propriedade para LogListParams."""

    @given(st.integers(min_value=1, max_value=1000))
    def test_log_list_params_accepts_positive_page(self, page: int) -> None:
        """Propriedade: page aceita qualquer inteiro >= 1."""
        params = LogListParams(page=page)
        assert params.page == page
        assert params.page >= 1

    @given(st.integers(min_value=1, max_value=100))
    def test_log_list_params_accepts_page_size_up_to_100(self, page_size: int) -> None:
        """Propriedade: page_size aceita qualquer inteiro entre 1 e 100."""
        params = LogListParams(page_size=page_size)
        assert params.page_size == page_size
        assert 1 <= params.page_size <= 100


# ============================================================================
# Testes de propriedade para AnalysisResult
# ============================================================================


class TestAnalysisResultProperties:
    """Testes de propriedade para AnalysisResult."""

    @given(
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=0, max_value=10000),
    )
    def test_analysis_result_accepts_non_negative_counters(
        self, total: int, errors: int, warnings: int
    ) -> None:
        """Propriedade: Contadores aceitam qualquer inteiro não-negativo."""
        result = AnalysisResult(
            total_entries=total,
            error_count=errors,
            warning_count=warnings,
        )
        assert result.total_entries >= 0
        assert result.error_count >= 0
        assert result.warning_count >= 0

    @given(st.booleans())
    def test_analysis_result_insufficient_data_flag(self, insufficient: bool) -> None:
        """Propriedade: insufficient_data flag é preservada."""
        result = AnalysisResult(insufficient_data=insufficient)
        assert result.insufficient_data == insufficient


# ============================================================================
# Testes de round-trip (serialização/desserialização)
# ============================================================================


class TestRoundTripProperties:
    """Testes de round-trip para garantir que serialização preserva dados."""

    @given(st.text(min_size=1, max_size=100))
    def test_log_entry_round_trip(self, raw_content: str) -> None:
        """Propriedade: LogEntry round-trip preserva dados."""
        # Hypothesis pode gerar strings que se tornam vazias após strip
        # Vamos garantir que o conteúdo não seja vazio após strip
        if not raw_content.strip():
            pytest.skip("raw_content vazio após strip")
        
        entry = LogEntry(raw_content=raw_content)
        data = entry.model_dump()
        restored = LogEntry(**data)
        assert restored.raw_content == entry.raw_content

    @given(hypothesis_strategy())
    def test_hypothesis_round_trip(self, hypothesis: Hypothesis) -> None:
        """Propriedade: Hypothesis round-trip preserva dados."""
        data = hypothesis.model_dump()
        restored = Hypothesis(**data)
        assert restored.description == hypothesis.description
        assert restored.probability == hypothesis.probability
        assert restored.action == hypothesis.action

    @given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
    def test_log_list_params_round_trip(self, page: int, page_size: int) -> None:
        """Propriedade: LogListParams round-trip preserva dados."""
        params = LogListParams(page=page, page_size=page_size)
        data = params.model_dump()
        restored = LogListParams(**data)
        assert restored.page == params.page
        assert restored.page_size == params.page_size
