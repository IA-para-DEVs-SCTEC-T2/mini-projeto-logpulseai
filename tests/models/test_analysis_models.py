"""Testes unitários e de propriedade para modelos de análise (Spike, AnalysisResult).

Valida os requisitos RF-04.2 e RF-04.4:
- Spike: pico de erros com validação de janela temporal e threshold
- AnalysisResult: resultado completo da análise de anomalias
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.schemas import (
    AnalysisResult,
    LogTemplate,
    SeverityLevel,
    Spike,
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
_LATER = _NOW + timedelta(seconds=60)


# ===========================================================================
# Spike — Testes unitários
# ===========================================================================


class TestSpikeModel:
    """Testes para o modelo Spike."""

    def test_valid_spike_creation(self) -> None:
        """Spike válido com campos obrigatórios."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        assert spike.start_time == _NOW
        assert spike.end_time == _LATER
        assert spike.error_count == 10

    def test_error_count_minimum_is_10(self) -> None:
        """error_count deve ser >= 10."""
        with pytest.raises(ValidationError):
            Spike(start_time=_NOW, end_time=_LATER, error_count=9)

    def test_error_count_exactly_10_accepted(self) -> None:
        """error_count = 10 é aceito (limite inferior)."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        assert spike.error_count == 10

    def test_end_time_must_be_after_start_time(self) -> None:
        """end_time deve ser posterior a start_time."""
        with pytest.raises(ValidationError):
            Spike(start_time=_LATER, end_time=_NOW, error_count=10)

    def test_equal_times_rejected(self) -> None:
        """start_time == end_time é rejeitado."""
        with pytest.raises(ValidationError):
            Spike(start_time=_NOW, end_time=_NOW, error_count=10)

    def test_template_ids_default_empty(self) -> None:
        """template_ids tem default de lista vazia."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        assert spike.template_ids == []

    def test_template_ids_accepts_list(self) -> None:
        """template_ids aceita lista de strings."""
        spike = Spike(
            start_time=_NOW,
            end_time=_LATER,
            error_count=15,
            template_ids=["tmpl-001", "tmpl-002"],
        )
        assert spike.template_ids == ["tmpl-001", "tmpl-002"]

    def test_large_error_count_accepted(self) -> None:
        """error_count grande é aceito."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10000)
        assert spike.error_count == 10000

    def test_spike_serialization(self) -> None:
        """Spike pode ser serializado para dict."""
        spike = Spike(
            start_time=_NOW,
            end_time=_LATER,
            error_count=12,
            template_ids=["t1"],
        )
        data = spike.model_dump()
        assert data["error_count"] == 12
        assert data["template_ids"] == ["t1"]

    def test_spike_json_roundtrip(self) -> None:
        """Spike pode ser serializado e deserializado via JSON."""
        spike = Spike(
            start_time=_NOW,
            end_time=_LATER,
            error_count=20,
            template_ids=["t1", "t2"],
        )
        json_str = spike.model_dump_json()
        restored = Spike.model_validate_json(json_str)
        assert restored.error_count == spike.error_count
        assert restored.template_ids == spike.template_ids


# ===========================================================================
# AnalysisResult — Testes unitários
# ===========================================================================


class TestAnalysisResultModel:
    """Testes para o modelo AnalysisResult."""

    def test_default_values(self) -> None:
        """AnalysisResult com defaults válidos."""
        result = AnalysisResult()
        assert result.total_entries == 0
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.spikes == []
        assert result.stack_traces == []
        assert result.templates == []
        assert result.insufficient_data is False
        assert result.severity_distribution == {}

    def test_total_entries_non_negative(self) -> None:
        """total_entries não pode ser negativo."""
        with pytest.raises(ValidationError):
            AnalysisResult(total_entries=-1)

    def test_error_count_non_negative(self) -> None:
        """error_count não pode ser negativo."""
        with pytest.raises(ValidationError):
            AnalysisResult(error_count=-1)

    def test_warning_count_non_negative(self) -> None:
        """warning_count não pode ser negativo."""
        with pytest.raises(ValidationError):
            AnalysisResult(warning_count=-1)

    def test_severity_distribution_accepts_all_levels(self) -> None:
        """severity_distribution aceita todos os SeverityLevel."""
        dist = {
            SeverityLevel.DEBUG: 5,
            SeverityLevel.INFO: 20,
            SeverityLevel.WARNING: 10,
            SeverityLevel.ERROR: 3,
            SeverityLevel.CRITICAL: 1,
        }
        result = AnalysisResult(total_entries=39, severity_distribution=dist)
        assert sum(result.severity_distribution.values()) == 39

    def test_spikes_list_accepts_valid_spikes(self) -> None:
        """spikes aceita lista de Spike válidos."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        result = AnalysisResult(total_entries=50, spikes=[spike])
        assert len(result.spikes) == 1

    def test_stack_traces_accepts_strings(self) -> None:
        """stack_traces aceita lista de strings."""
        traces = ["Traceback...\n  File...\nValueError: x"]
        result = AnalysisResult(total_entries=10, stack_traces=traces)
        assert len(result.stack_traces) == 1

    def test_templates_accepts_log_templates(self) -> None:
        """templates aceita lista de LogTemplate."""
        tmpl = LogTemplate(template_id="t1", pattern="error <*>", occurrences=5)
        result = AnalysisResult(total_entries=10, templates=[tmpl])
        assert len(result.templates) == 1

    def test_insufficient_data_flag(self) -> None:
        """insufficient_data pode ser True."""
        result = AnalysisResult(total_entries=1, insufficient_data=True)
        assert result.insufficient_data is True

    def test_analysis_result_serialization(self) -> None:
        """AnalysisResult pode ser serializado para dict."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        result = AnalysisResult(
            total_entries=100,
            error_count=15,
            warning_count=8,
            spikes=[spike],
            insufficient_data=False,
        )
        data = result.model_dump()
        assert data["total_entries"] == 100
        assert len(data["spikes"]) == 1

    def test_analysis_result_json_roundtrip(self) -> None:
        """AnalysisResult pode ser serializado e deserializado via JSON."""
        spike = Spike(start_time=_NOW, end_time=_LATER, error_count=10)
        result = AnalysisResult(
            total_entries=50,
            error_count=10,
            warning_count=5,
            spikes=[spike],
            severity_distribution={SeverityLevel.ERROR: 10, SeverityLevel.INFO: 40},
        )
        json_str = result.model_dump_json()
        restored = AnalysisResult.model_validate_json(json_str)
        assert restored.total_entries == 50
        assert len(restored.spikes) == 1


# ===========================================================================
# Property-Based Tests — Spike
# ===========================================================================


@given(
    start=st.datetimes(timezones=st.just(UTC)),
    delta=st.timedeltas(min_value=timedelta(seconds=1), max_value=timedelta(hours=24)),
    count=st.integers(min_value=10, max_value=10000),
)
@settings(max_examples=50)
def test_spike_always_valid_with_correct_params(
    start: datetime, delta: timedelta, count: int
) -> None:
    """Propriedade: Spike com end > start e count >= 10 é sempre válido."""
    end = start + delta
    spike = Spike(start_time=start, end_time=end, error_count=count)
    assert spike.end_time > spike.start_time
    assert spike.error_count >= 10


@given(count=st.integers(min_value=-100, max_value=9))
@settings(max_examples=30)
def test_spike_always_rejects_count_below_10(count: int) -> None:
    """Propriedade: error_count < 10 é sempre rejeitado."""
    with pytest.raises(ValidationError):
        Spike(start_time=_NOW, end_time=_LATER, error_count=count)


@given(
    delta=st.timedeltas(min_value=timedelta(seconds=0), max_value=timedelta(seconds=0)),
)
@settings(max_examples=10)
def test_spike_always_rejects_equal_times(delta: timedelta) -> None:
    """Propriedade: start_time == end_time é sempre rejeitado."""
    with pytest.raises(ValidationError):
        Spike(start_time=_NOW, end_time=_NOW + delta, error_count=10)


# ===========================================================================
# Property-Based Tests — AnalysisResult
# ===========================================================================


@given(
    total=st.integers(min_value=0, max_value=100000),
    errors=st.integers(min_value=0, max_value=100000),
    warnings=st.integers(min_value=0, max_value=100000),
)
@settings(max_examples=50)
def test_analysis_result_accepts_any_non_negative_counts(
    total: int, errors: int, warnings: int
) -> None:
    """Propriedade: qualquer combinação de contadores >= 0 é aceita."""
    result = AnalysisResult(
        total_entries=total,
        error_count=errors,
        warning_count=warnings,
    )
    assert result.total_entries == total
    assert result.error_count == errors
    assert result.warning_count == warnings


@given(total=st.integers(min_value=-1000, max_value=-1))
@settings(max_examples=20)
def test_analysis_result_rejects_negative_total(total: int) -> None:
    """Propriedade: total_entries negativo é sempre rejeitado."""
    with pytest.raises(ValidationError):
        AnalysisResult(total_entries=total)


@given(
    n_spikes=st.integers(min_value=0, max_value=5),
    count=st.integers(min_value=10, max_value=100),
)
@settings(max_examples=30)
def test_analysis_result_accepts_any_number_of_spikes(
    n_spikes: int, count: int
) -> None:
    """Propriedade: qualquer número de spikes válidos é aceito."""
    spikes = [
        Spike(
            start_time=_NOW + timedelta(minutes=i * 10),
            end_time=_NOW + timedelta(minutes=i * 10, seconds=30),
            error_count=count,
        )
        for i in range(n_spikes)
    ]
    result = AnalysisResult(total_entries=100, spikes=spikes)
    assert len(result.spikes) == n_spikes
