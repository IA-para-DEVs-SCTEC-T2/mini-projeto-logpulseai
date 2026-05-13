"""Detector de anomalias concreto para o LogPulse IA."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from src.analyzer.base import LogAnalyzer
from src.models.schemas import (
    AnalysisResult,
    LogEntry,
    LogTemplate,
    SeverityLevel,
    Spike,
)

# ---------------------------------------------------------------------------
# Constantes de detecção
# ---------------------------------------------------------------------------

# Janela de tempo para detecção de spikes (segundos)
_SPIKE_WINDOW_SECONDS = 60

# Mínimo de erros na janela para caracterizar spike
_SPIKE_THRESHOLD = 10

# Níveis considerados "erro" para detecção de spike
_ERROR_LEVELS = {SeverityLevel.ERROR, SeverityLevel.CRITICAL}

# Mínimo de entradas para análise confiável
_MIN_ENTRIES_FOR_ANALYSIS = 2

# ---------------------------------------------------------------------------
# Regex para detecção de stack traces
# ---------------------------------------------------------------------------

_RE_PYTHON_TRACEBACK = re.compile(
    r"Traceback \(most recent call last\)", re.IGNORECASE
)

_RE_JAVA_STACKTRACE = re.compile(
    r"(?:Exception in thread|at\s+[\w\.$]+\([\w\.]+\.java:\d+\))",
    re.IGNORECASE,
)

_RE_GO_PANIC = re.compile(
    r"(?:panic:|goroutine\s+\d+\s+\[)",
    re.IGNORECASE,
)


class AnomalyDetector(LogAnalyzer):
    """Detector de anomalias em streams de log.

    Implementa detecção de:
    - Distribuição de severidade por nível
    - Spikes de erro (≥10 erros ERROR/CRITICAL em janela de 60s)
    - Stack traces multi-linha (Python, Java, Go)
    - Agrupamento por template_id
    """

    def analyze(
        self,
        entries: List[LogEntry],
        templates: List[LogTemplate],
    ) -> AnalysisResult:
        """Analisa entradas de log e detecta anomalias.

        Args:
            entries: Lista de entradas de log normalizadas.
            templates: Templates extraídos pelo Drain3.

        Returns:
            AnalysisResult com distribuição, spikes e stack traces.
        """
        total = len(entries)

        # Dados insuficientes
        if total < _MIN_ENTRIES_FOR_ANALYSIS:
            return AnalysisResult(
                total_entries=total,
                insufficient_data=True,
                templates=templates,
            )

        severity_distribution = _compute_severity_distribution(entries)
        error_count = (
            severity_distribution.get(SeverityLevel.ERROR, 0)
            + severity_distribution.get(SeverityLevel.CRITICAL, 0)
        )
        warning_count = severity_distribution.get(SeverityLevel.WARNING, 0)

        spikes = _detect_spikes(entries)
        stack_traces = _extract_stack_traces(entries)

        return AnalysisResult(
            total_entries=total,
            severity_distribution=severity_distribution,
            error_count=error_count,
            warning_count=warning_count,
            spikes=spikes,
            stack_traces=stack_traces,
            templates=templates,
            insufficient_data=False,
        )


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------


def _compute_severity_distribution(
    entries: List[LogEntry],
) -> Dict[SeverityLevel, int]:
    """Calcula a distribuição de entradas por nível de severidade.

    Args:
        entries: Lista de entradas de log.

    Returns:
        Dicionário com contagem por SeverityLevel.
    """
    distribution: Dict[SeverityLevel, int] = defaultdict(int)
    for entry in entries:
        distribution[entry.severity] += 1
    return dict(distribution)


def _detect_spikes(entries: List[LogEntry]) -> List[Spike]:
    """Detecta spikes de erro usando janela deslizante de 60 segundos.

    Um spike é caracterizado por ≥10 erros (ERROR ou CRITICAL)
    em uma janela deslizante de 60 segundos.

    Args:
        entries: Lista de entradas de log ordenadas por timestamp.

    Returns:
        Lista de Spike detectados.
    """
    # Filtra apenas entradas de erro com timestamp válido
    error_entries = [
        e for e in entries
        if e.severity in _ERROR_LEVELS and e.timestamp is not None
    ]

    if len(error_entries) < _SPIKE_THRESHOLD:
        return []

    # Ordena por timestamp
    error_entries.sort(key=lambda e: e.timestamp)  # type: ignore[arg-type, return-value]

    spikes: List[Spike] = []
    window = timedelta(seconds=_SPIKE_WINDOW_SECONDS)
    i = 0

    while i < len(error_entries):
        start_ts = error_entries[i].timestamp
        assert start_ts is not None

        # Coleta todas as entradas dentro da janela
        window_entries = [
            e for e in error_entries[i:]
            if e.timestamp is not None and e.timestamp - start_ts <= window
        ]

        if len(window_entries) >= _SPIKE_THRESHOLD:
            end_ts = window_entries[-1].timestamp
            assert end_ts is not None

            # Garante que end_time > start_time
            if end_ts == start_ts:
                end_ts = start_ts + timedelta(seconds=1)

            template_ids = list({
                e.template_id for e in window_entries
                if e.template_id is not None
            })

            spikes.append(
                Spike(
                    start_time=start_ts,
                    end_time=end_ts,
                    error_count=len(window_entries),
                    template_ids=template_ids,
                )
            )
            # Avança para depois do fim da janela atual
            i += len(window_entries)
        else:
            i += 1

    return spikes


def _extract_stack_traces(entries: List[LogEntry]) -> List[str]:
    """Detecta e agrupa stack traces multi-linha nas entradas de log.

    Suporta:
    - Python: Traceback (most recent call last)
    - Java: Exception in thread / at ClassName.method(File.java:N)
    - Go: panic: / goroutine N [

    Args:
        entries: Lista de entradas de log.

    Returns:
        Lista de stack traces agrupados como strings.
    """
    stack_traces: List[str] = []
    current_trace: List[str] = []
    current_type: Optional[str] = None

    for entry in entries:
        raw = entry.raw_content

        if _RE_PYTHON_TRACEBACK.search(raw):
            if current_trace:
                stack_traces.append("\n".join(current_trace))
            current_trace = [raw]
            current_type = "python"

        elif _RE_JAVA_STACKTRACE.search(raw):
            if current_type == "java":
                current_trace.append(raw)
            else:
                if current_trace:
                    stack_traces.append("\n".join(current_trace))
                current_trace = [raw]
                current_type = "java"

        elif _RE_GO_PANIC.search(raw):
            if current_type == "go":
                current_trace.append(raw)
            else:
                if current_trace:
                    stack_traces.append("\n".join(current_trace))
                current_trace = [raw]
                current_type = "go"

        elif current_type == "python" and (
            raw.startswith("  ")
            or raw.startswith("\t")
            or raw.startswith("File ")
            or "Error:" in raw
            or "Exception:" in raw
            or "Warning:" in raw
        ):
            # Continuação de traceback Python
            # Nota: raw_content é stripped pelo modelo, então verificamos
            # tanto prefixos com espaço (caso não-stripped) quanto sem.
            current_trace.append(raw)

        elif current_type == "java" and (
            raw.strip().startswith("at ") or "Caused by:" in raw
        ):
            # Continuação de stacktrace Java
            current_trace.append(raw)

        elif current_type == "go" and (
            raw.strip().startswith("goroutine") or raw.strip().startswith("\t")
        ):
            # Continuação de panic Go
            current_trace.append(raw)

        else:
            # Linha não relacionada — fecha trace atual se existir
            if current_trace and len(current_trace) > 1:
                stack_traces.append("\n".join(current_trace))
            elif current_trace:
                # Trace de linha única — descarta
                pass
            current_trace = []
            current_type = None

    # Fecha trace pendente
    if current_trace and len(current_trace) > 1:
        stack_traces.append("\n".join(current_trace))

    return stack_traces
