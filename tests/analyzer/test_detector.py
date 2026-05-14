"""Testes unitários e de propriedade para o AnomalyDetector do LogPulse IA.

Cobre todos os critérios de aceitação da Tarefa 5:
- Interface abstrata LogAnalyzer
- Agrupamento por template_id
- Distribuição de severidade
- Detecção de spikes (janela deslizante de 60s, threshold ≥10)
- Agrupamento de stack traces (Python, Java, Go)
- Dados insuficientes (< 2 entradas)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analyzer.base import LogAnalyzer
from src.analyzer.detector import AnomalyDetector
from src.models.schemas import AnalysisResult, LogEntry, LogTemplate, SeverityLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_TIME = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


def make_entry(
    raw_content: str = "test log line",
    severity: SeverityLevel = SeverityLevel.INFO,
    timestamp: Optional[datetime] = None,
    template_id: Optional[str] = None,
) -> LogEntry:
    """Cria um LogEntry para uso nos testes."""
    return LogEntry(
        raw_content=raw_content,
        severity=severity,
        timestamp=timestamp or _BASE_TIME,
        template_id=template_id,
    )


def make_error_entries_in_window(
    count: int,
    window_seconds: int = 59,
    severity: SeverityLevel = SeverityLevel.ERROR,
    start_time: Optional[datetime] = None,
) -> List[LogEntry]:
    """Cria `count` entradas de erro distribuídas dentro de `window_seconds`."""
    base = start_time or _BASE_TIME
    entries = []
    for i in range(count):
        if count > 1:
            offset = timedelta(seconds=i * window_seconds / (count - 1)) if count > 1 else timedelta(0)
        else:
            offset = timedelta(0)
        entries.append(
            make_entry(
                raw_content=f"ERROR: failure {i}",
                severity=severity,
                timestamp=base + offset,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def detector() -> AnomalyDetector:
    """Instância limpa do AnomalyDetector para cada teste."""
    return AnomalyDetector()


# ===========================================================================
# Interface abstrata LogAnalyzer
# ===========================================================================


class TestLogAnalyzerInterface:
    def test_cannot_instantiate_abstract(self) -> None:
        """LogAnalyzer não pode ser instanciado diretamente."""
        with pytest.raises(TypeError):
            LogAnalyzer()  # type: ignore[abstract]

    def test_anomaly_detector_is_subclass(self) -> None:
        assert issubclass(AnomalyDetector, LogAnalyzer)

    def test_anomaly_detector_implements_analyze(self) -> None:
        d = AnomalyDetector()
        assert callable(d.analyze)

    def test_analyze_returns_analysis_result(self, detector: AnomalyDetector) -> None:
        entries = [make_entry(), make_entry()]
        result = detector.analyze(entries, [])
        assert isinstance(result, AnalysisResult)


# ===========================================================================
# Dados insuficientes
# ===========================================================================


class TestInsufficientData:
    def test_zero_entries_returns_insufficient_data(self, detector: AnomalyDetector) -> None:
        """0 entradas → insufficient_data=True."""
        result = detector.analyze([], [])
        assert result.insufficient_data is True
        assert result.total_entries == 0

    def test_one_entry_returns_insufficient_data(self, detector: AnomalyDetector) -> None:
        """1 entrada → insufficient_data=True."""
        result = detector.analyze([make_entry()], [])
        assert result.insufficient_data is True
        assert result.total_entries == 1

    def test_two_entries_not_insufficient(self, detector: AnomalyDetector) -> None:
        """2 entradas → insufficient_data=False."""
        entries = [make_entry(), make_entry()]
        result = detector.analyze(entries, [])
        assert result.insufficient_data is False

    def test_ten_entries_not_insufficient(self, detector: AnomalyDetector) -> None:
        """10 entradas → insufficient_data=False."""
        entries = [make_entry() for _ in range(10)]
        result = detector.analyze(entries, [])
        assert result.insufficient_data is False

    def test_hundred_entries_not_insufficient(self, detector: AnomalyDetector) -> None:
        """100 entradas → insufficient_data=False."""
        entries = [make_entry() for _ in range(100)]
        result = detector.analyze(entries, [])
        assert result.insufficient_data is False

    def test_insufficient_data_preserves_total_entries(self, detector: AnomalyDetector) -> None:
        """total_entries é preservado mesmo com dados insuficientes."""
        result = detector.analyze([make_entry()], [])
        assert result.total_entries == 1

    def test_insufficient_data_preserves_templates(self, detector: AnomalyDetector) -> None:
        """Templates são preservados mesmo com dados insuficientes."""
        template = LogTemplate(template_id="t1", pattern="test <*>", occurrences=1)
        result = detector.analyze([], [template])
        assert len(result.templates) == 1


# ===========================================================================
# Distribuição de severidade
# ===========================================================================


class TestSeverityDistribution:
    def test_single_severity_level(self, detector: AnomalyDetector) -> None:
        """Distribuição com apenas um nível de severidade."""
        entries = [make_entry(severity=SeverityLevel.ERROR) for _ in range(5)]
        entries.append(make_entry(severity=SeverityLevel.INFO))  # garante >= 2
        result = detector.analyze(entries, [])
        assert result.severity_distribution[SeverityLevel.ERROR] == 5
        assert result.severity_distribution[SeverityLevel.INFO] == 1

    def test_distribution_sums_to_total_entries(self, detector: AnomalyDetector) -> None:
        """Distribuição de severidade soma igual a total_entries."""
        entries = [
            make_entry(severity=SeverityLevel.DEBUG),
            make_entry(severity=SeverityLevel.INFO),
            make_entry(severity=SeverityLevel.WARNING),
            make_entry(severity=SeverityLevel.ERROR),
            make_entry(severity=SeverityLevel.CRITICAL),
        ]
        result = detector.analyze(entries, [])
        total_in_distribution = sum(result.severity_distribution.values())
        assert total_in_distribution == result.total_entries

    def test_distribution_all_levels(self, detector: AnomalyDetector) -> None:
        """Todos os níveis de severidade são contabilizados."""
        entries = []
        for level in SeverityLevel:
            entries.append(make_entry(severity=level))
        result = detector.analyze(entries, [])
        for level in SeverityLevel:
            assert result.severity_distribution.get(level, 0) == 1

    def test_error_count_includes_critical(self, detector: AnomalyDetector) -> None:
        """error_count inclui tanto ERROR quanto CRITICAL."""
        entries = [
            make_entry(severity=SeverityLevel.ERROR),
            make_entry(severity=SeverityLevel.CRITICAL),
            make_entry(severity=SeverityLevel.INFO),
        ]
        result = detector.analyze(entries, [])
        assert result.error_count == 2

    def test_warning_count_correct(self, detector: AnomalyDetector) -> None:
        """warning_count conta apenas WARNING."""
        entries = [
            make_entry(severity=SeverityLevel.WARNING),
            make_entry(severity=SeverityLevel.WARNING),
            make_entry(severity=SeverityLevel.ERROR),
        ]
        result = detector.analyze(entries, [])
        assert result.warning_count == 2

    def test_distribution_with_100_entries(self, detector: AnomalyDetector) -> None:
        """Distribuição correta com 100 entradas."""
        entries = []
        for i in range(100):
            level = list(SeverityLevel)[i % 5]
            entries.append(make_entry(severity=level))
        result = detector.analyze(entries, [])
        assert result.total_entries == 100
        assert sum(result.severity_distribution.values()) == 100


# ===========================================================================
# Agrupamento por template_id
# ===========================================================================


class TestTemplateGrouping:
    def test_entries_grouped_by_template_id(self, detector: AnomalyDetector) -> None:
        """AnomalyDetector agrupa LogEntry por template_id."""
        entries = [
            make_entry(template_id="tmpl-1"),
            make_entry(template_id="tmpl-1"),
            make_entry(template_id="tmpl-2"),
        ]
        result = detector.analyze(entries, [])
        # Análise deve completar sem erros e contar corretamente
        assert result.total_entries == 3

    def test_entries_without_template_id(self, detector: AnomalyDetector) -> None:
        """Entradas sem template_id são processadas normalmente."""
        entries = [make_entry(template_id=None), make_entry(template_id=None)]
        result = detector.analyze(entries, [])
        assert result.total_entries == 2

    def test_templates_passed_through(self, detector: AnomalyDetector) -> None:
        """Templates fornecidos são incluídos no resultado."""
        templates = [
            LogTemplate(template_id="t1", pattern="error <*>", occurrences=3),
            LogTemplate(template_id="t2", pattern="info <*>", occurrences=2),
        ]
        entries = [make_entry(), make_entry()]
        result = detector.analyze(entries, templates)
        assert len(result.templates) == 2


# ===========================================================================
# Detecção de spikes
# ===========================================================================


class TestSpikeDetection:
    def test_exactly_10_errors_in_60s_detects_spike(self, detector: AnomalyDetector) -> None:
        """Spike detectado com exatamente 10 erros em 60s."""
        entries = make_error_entries_in_window(10, window_seconds=59)
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1
        assert result.spikes[0].error_count >= 10

    def test_15_errors_in_60s_detects_spike(self, detector: AnomalyDetector) -> None:
        """Spike detectado com 15 erros em 60s."""
        entries = make_error_entries_in_window(15, window_seconds=59)
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1

    def test_9_errors_in_60s_no_spike(self, detector: AnomalyDetector) -> None:
        """Sem spike com 9 erros em 60s."""
        entries = make_error_entries_in_window(9, window_seconds=59)
        result = detector.analyze(entries, [])
        assert len(result.spikes) == 0

    def test_10_errors_in_61s_no_spike(self, detector: AnomalyDetector) -> None:
        """Sem spike com 10 erros em 61s (fora da janela de 60s)."""
        base = _BASE_TIME
        entries = []
        for i in range(10):
            # Distribui 10 erros em 61 segundos (cada um separado por ~6.8s)
            offset = timedelta(seconds=i * 61 / 9)
            entries.append(
                make_entry(
                    raw_content=f"ERROR: failure {i}",
                    severity=SeverityLevel.ERROR,
                    timestamp=base + offset,
                )
            )
        result = detector.analyze(entries, [])
        assert len(result.spikes) == 0

    def test_spike_error_count_correct(self, detector: AnomalyDetector) -> None:
        """error_count do spike reflete o número de erros na janela."""
        entries = make_error_entries_in_window(12, window_seconds=30)
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1
        assert result.spikes[0].error_count == 12

    def test_spike_with_critical_severity(self, detector: AnomalyDetector) -> None:
        """CRITICAL também conta para detecção de spike."""
        entries = make_error_entries_in_window(10, window_seconds=59, severity=SeverityLevel.CRITICAL)
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1

    def test_spike_mixed_error_and_critical(self, detector: AnomalyDetector) -> None:
        """Mistura de ERROR e CRITICAL conta para spike."""
        base = _BASE_TIME
        entries = []
        for i in range(5):
            entries.append(make_entry(severity=SeverityLevel.ERROR, timestamp=base + timedelta(seconds=i * 5)))
        for i in range(5):
            entries.append(make_entry(severity=SeverityLevel.CRITICAL, timestamp=base + timedelta(seconds=25 + i * 5)))
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1

    def test_warnings_do_not_trigger_spike(self, detector: AnomalyDetector) -> None:
        """WARNING não conta para detecção de spike."""
        entries = make_error_entries_in_window(15, window_seconds=30, severity=SeverityLevel.WARNING)
        result = detector.analyze(entries, [])
        assert len(result.spikes) == 0

    def test_info_does_not_trigger_spike(self, detector: AnomalyDetector) -> None:
        """INFO não conta para detecção de spike."""
        entries = make_error_entries_in_window(20, window_seconds=30, severity=SeverityLevel.INFO)
        result = detector.analyze(entries, [])
        assert len(result.spikes) == 0

    def test_spike_start_time_before_end_time(self, detector: AnomalyDetector) -> None:
        """Spike tem start_time < end_time."""
        entries = make_error_entries_in_window(10, window_seconds=30)
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1
        for spike in result.spikes:
            assert spike.end_time > spike.start_time

    def test_no_spike_with_zero_errors(self, detector: AnomalyDetector) -> None:
        """Sem erros → sem spike."""
        entries = [make_entry(severity=SeverityLevel.INFO) for _ in range(20)]
        result = detector.analyze(entries, [])
        assert len(result.spikes) == 0

    def test_spike_with_template_ids(self, detector: AnomalyDetector) -> None:
        """Spike inclui template_ids das entradas envolvidas."""
        base = _BASE_TIME
        entries = []
        for i in range(10):
            entries.append(
                make_entry(
                    severity=SeverityLevel.ERROR,
                    timestamp=base + timedelta(seconds=i * 5),
                    template_id="tmpl-error",
                )
            )
        result = detector.analyze(entries, [])
        assert len(result.spikes) >= 1
        assert "tmpl-error" in result.spikes[0].template_ids


# ===========================================================================
# Agrupamento de stack traces
# ===========================================================================


class TestStackTraceDetection:
    def test_python_traceback_grouped_in_one_event(self, detector: AnomalyDetector) -> None:
        """Python traceback multi-linha agrupado em 1 evento."""
        entries = [
            make_entry(raw_content="Traceback (most recent call last):"),
            make_entry(raw_content='  File "app.py", line 42, in main'),
            make_entry(raw_content="    result = process()"),
            make_entry(raw_content="ValueError: invalid input"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 1
        assert "Traceback" in result.stack_traces[0]

    def test_java_stacktrace_grouped_in_one_event(self, detector: AnomalyDetector) -> None:
        """Java stacktrace multi-linha agrupado em 1 evento."""
        entries = [
            make_entry(raw_content="Exception in thread main java.lang.NullPointerException"),
            make_entry(raw_content="    at com.example.App.main(App.java:10)"),
            make_entry(raw_content="    at com.example.App.run(App.java:20)"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 1
        assert "Exception in thread" in result.stack_traces[0]

    def test_go_panic_grouped_in_one_event(self, detector: AnomalyDetector) -> None:
        """Go panic multi-linha agrupado em 1 evento."""
        entries = [
            make_entry(raw_content="panic: runtime error: index out of range"),
            make_entry(raw_content="goroutine 1 [running]:"),
            make_entry(raw_content="\tmain.main()"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 1
        assert "panic:" in result.stack_traces[0]

    def test_python_traceback_preserves_order(self, detector: AnomalyDetector) -> None:
        """Linhas do traceback Python são preservadas em ordem."""
        lines = [
            "Traceback (most recent call last):",
            "File app.py line 10 in handler",
            "RuntimeError: oops",
        ]
        entries = [make_entry(raw_content=line) for line in lines]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 1
        trace = result.stack_traces[0]
        assert trace.index("Traceback") < trace.index("RuntimeError")

    def test_no_stack_traces_in_normal_logs(self, detector: AnomalyDetector) -> None:
        """Logs normais não geram stack traces."""
        entries = [
            make_entry(raw_content="INFO: server started"),
            make_entry(raw_content="INFO: request received"),
            make_entry(raw_content="ERROR: connection refused"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 0

    def test_multiple_stack_traces_detected(self, detector: AnomalyDetector) -> None:
        """Múltiplos stack traces são detectados separadamente."""
        entries = [
            make_entry(raw_content="Traceback (most recent call last):"),
            make_entry(raw_content='  File "a.py", line 1, in foo'),
            make_entry(raw_content="ValueError: first error"),
            make_entry(raw_content="INFO: recovered"),
            make_entry(raw_content="Traceback (most recent call last):"),
            make_entry(raw_content='  File "b.py", line 2, in bar'),
            make_entry(raw_content="TypeError: second error"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 2

    def test_java_stacktrace_continuation_lines(self, detector: AnomalyDetector) -> None:
        """Linhas 'at ...' continuam o stacktrace Java."""
        entries = [
            make_entry(raw_content="Exception in thread main java.io.IOException"),
            make_entry(raw_content="    at java.io.FileInputStream.open(FileInputStream.java:195)"),
            make_entry(raw_content="    at java.io.FileInputStream.<init>(FileInputStream.java:138)"),
            make_entry(raw_content="Caused by: java.io.FileNotFoundException: file.txt"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 1
        assert "Caused by" in result.stack_traces[0]

    def test_go_panic_goroutine_continuation(self, detector: AnomalyDetector) -> None:
        """Linhas goroutine continuam o panic Go."""
        entries = [
            make_entry(raw_content="panic: nil pointer dereference"),
            make_entry(raw_content="goroutine 1 [running]:"),
            make_entry(raw_content="\tmain.handler(0xc000012345)"),
        ]
        result = detector.analyze(entries, [])
        assert len(result.stack_traces) == 1


# ===========================================================================
# Casos de borda: 0, 1, 2, 10, 100 entradas
# ===========================================================================


class TestEntryCounts:
    def test_zero_entries(self, detector: AnomalyDetector) -> None:
        """0 entradas → resultado válido com insufficient_data=True."""
        result = detector.analyze([], [])
        assert result.total_entries == 0
        assert result.insufficient_data is True
        assert result.spikes == []
        assert result.stack_traces == []

    def test_one_entry(self, detector: AnomalyDetector) -> None:
        """1 entrada → resultado válido com insufficient_data=True."""
        result = detector.analyze([make_entry()], [])
        assert result.total_entries == 1
        assert result.insufficient_data is True

    def test_two_entries(self, detector: AnomalyDetector) -> None:
        """2 entradas → análise completa sem insufficient_data."""
        entries = [make_entry(), make_entry()]
        result = detector.analyze(entries, [])
        assert result.total_entries == 2
        assert result.insufficient_data is False
        assert sum(result.severity_distribution.values()) == 2

    def test_ten_entries(self, detector: AnomalyDetector) -> None:
        """10 entradas → análise completa."""
        entries = [make_entry() for _ in range(10)]
        result = detector.analyze(entries, [])
        assert result.total_entries == 10
        assert result.insufficient_data is False
        assert sum(result.severity_distribution.values()) == 10

    def test_hundred_entries(self, detector: AnomalyDetector) -> None:
        """100 entradas → análise completa."""
        entries = [make_entry() for _ in range(100)]
        result = detector.analyze(entries, [])
        assert result.total_entries == 100
        assert result.insufficient_data is False
        assert sum(result.severity_distribution.values()) == 100


# ===========================================================================
# Property-based tests (hypothesis)
# ===========================================================================

_severity_strategy = st.sampled_from(list(SeverityLevel))


@given(
    n=st.integers(min_value=2, max_value=100),
    severities=st.lists(
        st.sampled_from(list(SeverityLevel)),
        min_size=2,
        max_size=100,
    ),
)
@settings(max_examples=50)
def test_severity_distribution_always_sums_to_total_entries(
    n: int, severities: list[SeverityLevel]
) -> None:
    """**Validates: Requirements RF-04.4**

    Propriedade: distribuição de severidade sempre soma igual a total_entries.
    """
    detector = AnomalyDetector()
    entries = [
        make_entry(severity=severities[i % len(severities)])
        for i in range(len(severities))
    ]
    result = detector.analyze(entries, [])
    if not result.insufficient_data:
        total_in_dist = sum(result.severity_distribution.values())
        assert total_in_dist == result.total_entries


@given(n=st.integers(min_value=0, max_value=1))
@settings(max_examples=20)
def test_insufficient_data_always_true_when_less_than_2(n: int) -> None:
    """**Validates: Requirements RF-04.5**

    Propriedade: insufficient_data=True sempre que há < 2 entradas.
    """
    detector = AnomalyDetector()
    entries = [make_entry() for _ in range(n)]
    result = detector.analyze(entries, [])
    assert result.insufficient_data is True


@given(
    extra=st.integers(min_value=0, max_value=20),
)
@settings(max_examples=30)
def test_spike_always_has_error_count_gte_10(extra: int) -> None:
    """**Validates: Requirements RF-04.2**

    Propriedade: todo spike detectado tem error_count >= 10.
    """
    detector = AnomalyDetector()
    base = _BASE_TIME
    count = 10 + extra
    entries = []
    for i in range(count):
        offset = timedelta(seconds=i * 59 / max(count - 1, 1))
        entries.append(
            make_entry(
                severity=SeverityLevel.ERROR,
                timestamp=base + offset,
            )
        )
    result = detector.analyze(entries, [])
    for spike in result.spikes:
        assert spike.error_count >= 10


@given(
    n=st.integers(min_value=2, max_value=50),
)
@settings(max_examples=30)
def test_total_entries_always_matches_input_length(n: int) -> None:
    """Propriedade: total_entries sempre reflete o número de entradas fornecidas."""
    detector = AnomalyDetector()
    entries = [make_entry() for _ in range(n)]
    result = detector.analyze(entries, [])
    assert result.total_entries == n
