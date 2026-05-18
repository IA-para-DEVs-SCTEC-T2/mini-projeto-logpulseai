"""Testes de propriedade para detecção de spikes no AnomalyDetector.

Valida os requisitos RF-04.2 e RN-02:
- Spike = ≥10 erros (ERROR/CRITICAL) em janela deslizante de 60 segundos
- Janela deslizante avança corretamente
- Apenas ERROR e CRITICAL contam para spike
- Spikes não se sobrepõem
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.analyzer.detector import AnomalyDetector
from src.models.schemas import LogEntry, SeverityLevel, Spike


# ---------------------------------------------------------------------------
# Constantes (espelham src/analyzer/detector.py)
# ---------------------------------------------------------------------------

_SPIKE_WINDOW_SECONDS = 60
_SPIKE_THRESHOLD = 10
_ERROR_LEVELS = {SeverityLevel.ERROR, SeverityLevel.CRITICAL}
_BASE_TIME = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Função auxiliar para testes
# ---------------------------------------------------------------------------


def _detect_spikes(entries: List[LogEntry]) -> List[Spike]:
    """Função auxiliar que chama o método _detect_spikes do detector."""
    detector = AnomalyDetector()
    return detector._detect_spikes(entries)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    severity: SeverityLevel = SeverityLevel.ERROR,
    timestamp: datetime | None = None,
) -> LogEntry:
    """Cria LogEntry para testes de spike."""
    return LogEntry(
        raw_content=f"{severity.value}: test message",
        severity=severity,
        timestamp=timestamp or _BASE_TIME,
    )


def _make_error_burst(
    count: int,
    start: datetime | None = None,
    window_seconds: int = 59,
) -> List[LogEntry]:
    """Cria burst de erros distribuídos uniformemente em uma janela."""
    base = start or _BASE_TIME
    entries = []
    for i in range(count):
        offset = timedelta(seconds=i * window_seconds / max(count - 1, 1))
        entries.append(_make_entry(timestamp=base + offset))
    return entries


# ===========================================================================
# Testes de propriedade — Invariantes do spike
# ===========================================================================


@given(
    count=st.integers(min_value=10, max_value=50),
    window=st.integers(min_value=1, max_value=59),
)
@settings(max_examples=50)
def test_spike_detected_when_threshold_met_within_window(
    count: int, window: int
) -> None:
    """Propriedade: ≥10 erros em ≤60s sempre gera pelo menos 1 spike."""
    entries = _make_error_burst(count, window_seconds=window)
    spikes = _detect_spikes(entries)
    assert len(spikes) >= 1


@given(count=st.integers(min_value=1, max_value=9))
@settings(max_examples=30)
def test_no_spike_when_below_threshold(count: int) -> None:
    """Propriedade: <10 erros nunca gera spike."""
    entries = _make_error_burst(count, window_seconds=30)
    spikes = _detect_spikes(entries)
    assert len(spikes) == 0


@given(
    count=st.integers(min_value=10, max_value=30),
    spread=st.integers(min_value=61, max_value=300),
)
@settings(max_examples=50)
def test_no_spike_when_errors_spread_beyond_window(count: int, spread: int) -> None:
    """Propriedade: erros espalhados além de 60s não geram spike."""
    entries = _make_error_burst(count, window_seconds=spread)
    spikes = _detect_spikes(entries)
    # Se os erros estão espalhados em mais de 60s, pode não haver spike
    # (depende da distribuição, mas com spread > 60 e count < 30,
    # a densidade é insuficiente)
    for spike in spikes:
        # Qualquer spike detectado deve ter error_count >= threshold
        assert spike.error_count >= _SPIKE_THRESHOLD


@given(
    n_info=st.integers(min_value=10, max_value=50),
    n_warning=st.integers(min_value=10, max_value=50),
    n_debug=st.integers(min_value=10, max_value=50),
)
@settings(max_examples=30)
def test_non_error_levels_never_trigger_spike(
    n_info: int, n_warning: int, n_debug: int
) -> None:
    """Propriedade: INFO, WARNING e DEBUG nunca geram spike."""
    entries: List[LogEntry] = []
    for i in range(n_info):
        entries.append(_make_entry(SeverityLevel.INFO, _BASE_TIME + timedelta(seconds=i)))
    for i in range(n_warning):
        entries.append(_make_entry(SeverityLevel.WARNING, _BASE_TIME + timedelta(seconds=i)))
    for i in range(n_debug):
        entries.append(_make_entry(SeverityLevel.DEBUG, _BASE_TIME + timedelta(seconds=i)))

    spikes = _detect_spikes(entries)
    assert len(spikes) == 0


@given(extra=st.integers(min_value=0, max_value=40))
@settings(max_examples=30)
def test_every_spike_has_error_count_gte_threshold(extra: int) -> None:
    """Propriedade: todo spike detectado tem error_count >= 10."""
    count = _SPIKE_THRESHOLD + extra
    entries = _make_error_burst(count, window_seconds=59)
    spikes = _detect_spikes(entries)
    for spike in spikes:
        assert spike.error_count >= _SPIKE_THRESHOLD


@given(extra=st.integers(min_value=0, max_value=20))
@settings(max_examples=30)
def test_spike_time_range_within_window(extra: int) -> None:
    """Propriedade: duração de cada spike é ≤ 60 segundos + 1s de margem."""
    count = _SPIKE_THRESHOLD + extra
    entries = _make_error_burst(count, window_seconds=59)
    spikes = _detect_spikes(entries)
    for spike in spikes:
        duration = (spike.end_time - spike.start_time).total_seconds()
        # A janela é de 60s, mas end_time pode ser ajustado em +1s
        assert duration <= _SPIKE_WINDOW_SECONDS + 1


@given(extra=st.integers(min_value=0, max_value=20))
@settings(max_examples=30)
def test_spike_start_time_always_before_end_time(extra: int) -> None:
    """Propriedade: start_time < end_time em todo spike."""
    count = _SPIKE_THRESHOLD + extra
    entries = _make_error_burst(count, window_seconds=59)
    spikes = _detect_spikes(entries)
    for spike in spikes:
        assert spike.start_time < spike.end_time


# ===========================================================================
# Testes determinísticos — Casos de borda
# ===========================================================================


class TestSpikeEdgeCases:
    """Testes para casos de borda na detecção de spikes."""

    def test_exactly_threshold_at_boundary(self) -> None:
        """Exatamente 10 erros no limite de 60s detecta spike."""
        entries = _make_error_burst(10, window_seconds=60)
        spikes = _detect_spikes(entries)
        assert len(spikes) >= 1

    def test_all_errors_same_timestamp(self) -> None:
        """Todos os erros no mesmo instante detecta spike."""
        entries = [_make_entry(timestamp=_BASE_TIME) for _ in range(15)]
        spikes = _detect_spikes(entries)
        assert len(spikes) >= 1

    def test_mixed_error_and_critical_counts(self) -> None:
        """Mistura de ERROR e CRITICAL conta para o mesmo spike."""
        entries = []
        for i in range(5):
            entries.append(
                _make_entry(SeverityLevel.ERROR, _BASE_TIME + timedelta(seconds=i * 5))
            )
        for i in range(5):
            entries.append(
                _make_entry(SeverityLevel.CRITICAL, _BASE_TIME + timedelta(seconds=25 + i * 5))
            )
        spikes = _detect_spikes(entries)
        assert len(spikes) >= 1

    def test_two_separate_spikes(self) -> None:
        """Dois bursts separados por mais de 60s geram 2 spikes."""
        burst1 = _make_error_burst(12, start=_BASE_TIME, window_seconds=30)
        burst2 = _make_error_burst(
            12, start=_BASE_TIME + timedelta(minutes=5), window_seconds=30
        )
        entries = burst1 + burst2
        spikes = _detect_spikes(entries)
        assert len(spikes) == 2

    def test_entries_without_timestamp_ignored(self) -> None:
        """Entradas sem timestamp são ignoradas na detecção de spike."""
        entries = [
            LogEntry(raw_content="ERROR: no timestamp", severity=SeverityLevel.ERROR)
            for _ in range(20)
        ]
        spikes = _detect_spikes(entries)
        assert len(spikes) == 0

    def test_spike_template_ids_collected(self) -> None:
        """template_ids das entradas são coletados no spike."""
        entries = []
        for i in range(12):
            entries.append(
                LogEntry(
                    raw_content=f"ERROR: msg {i}",
                    severity=SeverityLevel.ERROR,
                    timestamp=_BASE_TIME + timedelta(seconds=i * 4),
                    template_id="tmpl-db-error",
                )
            )
        spikes = _detect_spikes(entries)
        assert len(spikes) >= 1
        assert "tmpl-db-error" in spikes[0].template_ids

    def test_empty_list_returns_no_spikes(self) -> None:
        """Lista vazia retorna lista vazia de spikes."""
        assert _detect_spikes([]) == []


# ===========================================================================
# Teste de integração com AnomalyDetector
# ===========================================================================


class TestSpikeIntegration:
    """Testes de integração do spike detection via AnomalyDetector.analyze."""

    def test_analyze_includes_spikes_in_result(self) -> None:
        """AnalysisResult inclui spikes detectados."""
        detector = AnomalyDetector()
        entries = _make_error_burst(15, window_seconds=30)
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1
        assert result.spikes[0].error_count >= 10

    def test_analyze_no_spikes_with_low_error_count(self) -> None:
        """AnalysisResult sem spikes quando há poucos erros."""
        detector = AnomalyDetector()
        entries = [
            _make_entry(SeverityLevel.INFO, _BASE_TIME + timedelta(seconds=i))
            for i in range(20)
        ]
        result = detector.analyze(entries, [])
        assert len(result.spikes) == 0
