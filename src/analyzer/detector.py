"""Implementação concreta do detector de anomalias em logs."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta

from src.analyzer.base import LogAnalyzer
from src.core.logging import get_logger
from src.models.schemas import (
    AnalysisResult,
    LogEntry,
    LogTemplate,
    SeverityLevel,
    Spike,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes de configuração
# ---------------------------------------------------------------------------

# Threshold para detecção de spike: mínimo de erros na janela
_SPIKE_THRESHOLD = 10

# Janela deslizante para detecção de spike (em segundos)
_SPIKE_WINDOW_SECONDS = 60

# Regex para detecção de stack traces
_RE_PYTHON_TRACEBACK = re.compile(r"Traceback \(most recent call last\)")
_RE_PYTHON_CONTINUATION = re.compile(r"^\s+(File |.*Error|.*Exception)")

_RE_JAVA_EXCEPTION = re.compile(r"(Exception in thread|^\s+at .+\(.+\.\w+:\d+\))")
_RE_JAVA_CONTINUATION = re.compile(r"^\s+at |^Caused by:")

_RE_GO_PANIC = re.compile(r"(panic: |goroutine \d+)")
_RE_GO_CONTINUATION = re.compile(r"^\s+\S|^goroutine \d+")


class AnomalyDetector(LogAnalyzer):
    """Detector de anomalias concreto para análise de logs.

    Implementa a interface LogAnalyzer para detectar anomalias em streams
    de log, incluindo:
    - Agrupamento por template_id (RF-04.1)
    - Cálculo de distribuição de severidade (RF-04.4)
    - Detecção de spikes de erro (RF-04.2, RN-02)
    - Agrupamento de stack traces (RF-04.3)
    - Validação de dados insuficientes (RF-04.5)
    """

    def analyze(self, entries: list[LogEntry], templates: list[LogTemplate]) -> AnalysisResult:
        """Analisa um stream de logs e detecta anomalias.

        Args:
            entries: Lista de entradas de log normalizadas pelo parser.
            templates: Lista de templates extraídos pelo Drain3.

        Returns:
            AnalysisResult contendo anomalias detectadas, distribuição
            de severidade, spikes e metadados da análise.
        """
        logger.info(
            "analysis_started",
            total_entries=len(entries),
            total_templates=len(templates)
        )
        
        # Verifica dados insuficientes (RF-04.5)
        if len(entries) < 2:
            logger.warning(
                "insufficient_data",
                total_entries=len(entries),
                minimum_required=2
            )
            return AnalysisResult(
                total_entries=len(entries),
                templates=templates,
                insufficient_data=True,
            )

        # Calcula distribuição de severidade (RF-04.4)
        severity_distribution = self._calculate_severity_distribution(entries)
        
        logger.debug(
            "severity_distribution_calculated",
            distribution={k.value: v for k, v in severity_distribution.items()}
        )

        # Conta erros e warnings
        error_count = severity_distribution.get(SeverityLevel.ERROR, 0) + severity_distribution.get(
            SeverityLevel.CRITICAL, 0
        )
        warning_count = severity_distribution.get(SeverityLevel.WARNING, 0)

        # Agrupa entradas por template_id (RF-04.1)
        self._group_by_template(entries)

        # Detecta spikes de erro (RF-04.2, RN-02)
        spikes = self._detect_spikes(entries)
        
        if spikes:
            logger.warning(
                "spikes_detected",
                spike_count=len(spikes),
                spikes=[
                    {
                        "start_time": spike.start_time.isoformat(),
                        "end_time": spike.end_time.isoformat(),
                        "error_count": spike.error_count,
                        "template_ids": spike.template_ids
                    }
                    for spike in spikes
                ]
            )

        # Detecta e agrupa stack traces (RF-04.3)
        stack_traces = self._detect_stack_traces(entries)
        
        if stack_traces:
            logger.info(
                "stack_traces_detected",
                stack_trace_count=len(stack_traces)
            )
        
        logger.info(
            "analysis_completed",
            total_entries=len(entries),
            error_count=error_count,
            warning_count=warning_count,
            spike_count=len(spikes),
            stack_trace_count=len(stack_traces)
        )

        return AnalysisResult(
            total_entries=len(entries),
            severity_distribution=severity_distribution,
            error_count=error_count,
            warning_count=warning_count,
            spikes=spikes,
            stack_traces=stack_traces,
            templates=templates,
            insufficient_data=False,
        )

    def _calculate_severity_distribution(self, entries: list[LogEntry]) -> dict[SeverityLevel, int]:
        """Calcula a distribuição de entradas por nível de severidade.

        Args:
            entries: Lista de entradas de log.

        Returns:
            Dicionário mapeando SeverityLevel para contagem de ocorrências.
        """
        distribution: dict[SeverityLevel, int] = defaultdict(int)
        for entry in entries:
            distribution[entry.severity] += 1
        return dict(distribution)

    def _group_by_template(self, entries: list[LogEntry]) -> dict[str, list[LogEntry]]:
        """Agrupa entradas de log por template_id.

        Args:
            entries: Lista de entradas de log.

        Returns:
            Dicionário mapeando template_id para lista de entradas.
        """
        groups: dict[str, list[LogEntry]] = defaultdict(list)
        for entry in entries:
            if entry.template_id:
                groups[entry.template_id].append(entry)
        return dict(groups)

    def _detect_spikes(self, entries: list[LogEntry]) -> list[Spike]:
        """Detecta spikes de erro usando janela deslizante.

        Um spike é definido como ≥10 erros (ERROR ou CRITICAL) em uma
        janela deslizante de 60 segundos (RN-02).

        Args:
            entries: Lista de entradas de log.

        Returns:
            Lista de Spike detectados.
        """
        # Filtra apenas entradas com timestamp e severidade ERROR/CRITICAL
        critical_levels = {SeverityLevel.ERROR, SeverityLevel.CRITICAL}
        error_entries = [
            e for e in entries if e.severity in critical_levels and e.timestamp is not None
        ]

        if len(error_entries) < _SPIKE_THRESHOLD:
            return []

        # Ordena por timestamp
        error_entries.sort(key=lambda e: e.timestamp or e.timestamp)  # type: ignore[arg-type, return-value]

        spikes: list[Spike] = []
        window = timedelta(seconds=_SPIKE_WINDOW_SECONDS)
        n = len(error_entries)
        i = 0

        while i < n:
            # Encontra o fim da janela a partir de error_entries[i]
            start_ts = error_entries[i].timestamp
            assert start_ts is not None

            # Conta entradas dentro da janela
            j = i
            while j < n:
                entry_ts = error_entries[j].timestamp
                assert entry_ts is not None
                if entry_ts - start_ts >= window:
                    break
                j += 1

            count_in_window = j - i

            if count_in_window >= _SPIKE_THRESHOLD:
                end_ts = error_entries[j - 1].timestamp
                assert end_ts is not None

                # Coleta template_ids únicos das entradas no spike
                template_ids = list(
                    {e.template_id for e in error_entries[i:j] if e.template_id is not None}
                )

                spikes.append(
                    Spike(
                        start_time=start_ts,
                        end_time=end_ts + timedelta(milliseconds=1),
                        error_count=count_in_window,
                        template_ids=template_ids,
                    )
                )
                # Avança para depois do spike para evitar sobreposição
                i = j
            else:
                i += 1

        return spikes

    def _detect_stack_traces(self, entries: list[LogEntry]) -> list[str]:
        """Detecta e agrupa stack traces multi-linha.

        Suporta:
        - Python traceback (Traceback (most recent call last):)
        - Java stacktrace (Exception in thread / at ...)
        - Go panic (panic: / goroutine N)

        Args:
            entries: Lista de entradas de log.

        Returns:
            Lista de stack traces agrupados como strings.
        """
        stack_traces: list[str] = []
        i = 0
        n = len(entries)

        while i < n:
            raw = entries[i].raw_content

            # Detecta início de Python traceback
            if _RE_PYTHON_TRACEBACK.search(raw):
                trace_lines = [raw]
                i += 1
                while i < n:
                    next_raw = entries[i].raw_content
                    # Continua se é indentação, File, Error ou Exception
                    if (
                        next_raw.startswith("  ")
                        or next_raw.startswith("\t")
                        or next_raw.startswith("File ")
                        or "Error:" in next_raw
                        or "Error " in next_raw
                        or "Exception:" in next_raw
                        or "Exception " in next_raw
                    ):
                        trace_lines.append(next_raw)
                        i += 1
                    else:
                        break
                stack_traces.append("\n".join(trace_lines))
                continue

            # Detecta início de Java stacktrace
            if re.search(r"Exception in thread", raw):
                trace_lines = [raw]
                i += 1
                while i < n:
                    next_raw = entries[i].raw_content
                    if _RE_JAVA_CONTINUATION.search(next_raw) or next_raw.strip().startswith("at "):
                        trace_lines.append(next_raw)
                        i += 1
                    else:
                        break
                stack_traces.append("\n".join(trace_lines))
                continue

            # Detecta início de Go panic
            if re.search(r"^panic: ", raw):
                trace_lines = [raw]
                i += 1
                while i < n:
                    next_raw = entries[i].raw_content
                    if _RE_GO_CONTINUATION.search(next_raw):
                        trace_lines.append(next_raw)
                        i += 1
                    else:
                        break
                stack_traces.append("\n".join(trace_lines))
                continue

            i += 1

        return stack_traces
