"""Motor de análise de logs: detecção de anomalias e spikes de erros."""

from __future__ import annotations

from collections import Counter
from datetime import timedelta

from logpulse.models import AnalysisResult, LogEntry, SeverityLevel

# Limiar de spike: mais de N erros em uma janela de tempo
_SPIKE_THRESHOLD = 10
_SPIKE_WINDOW = timedelta(minutes=1)


class Analyzer:
    """Analisa uma lista de LogEntry e detecta anomalias e spikes."""

    def analyze(self, entries: list[LogEntry]) -> AnalysisResult:
        """
        Executa análise completa sobre as entradas de log.

        Detecta spikes de erros e agrupa padrões de mensagens repetidas.
        """
        if not entries:
            return AnalysisResult(total_entries=0, error_count=0, warning_count=0)

        error_count = sum(1 for e in entries if e.level in {SeverityLevel.ERROR, SeverityLevel.CRITICAL})
        warning_count = sum(1 for e in entries if e.level == SeverityLevel.WARNING)

        spikes = self._detect_spikes(entries)
        anomalies = self._detect_anomalies(entries)

        return AnalysisResult(
            total_entries=len(entries),
            error_count=error_count,
            warning_count=warning_count,
            spikes=spikes,
            anomalies=anomalies,
        )

    def _detect_spikes(self, entries: list[LogEntry]) -> list[str]:
        """Detecta janelas de tempo com concentração anormal de erros."""
        errors = sorted(
            [e for e in entries if e.level in {SeverityLevel.ERROR, SeverityLevel.CRITICAL}],
            key=lambda e: e.timestamp,
        )
        spikes: list[str] = []
        i = 0
        while i < len(errors):
            window_end = errors[i].timestamp + _SPIKE_WINDOW
            count = sum(1 for e in errors if errors[i].timestamp <= e.timestamp <= window_end)
            if count >= _SPIKE_THRESHOLD:
                spikes.append(
                    f"Spike de {count} erros entre {errors[i].timestamp.isoformat()} e {window_end.isoformat()}"
                )
                i += count
            else:
                i += 1
        return spikes

    def _detect_anomalies(self, entries: list[LogEntry]) -> list[str]:
        """Detecta mensagens de erro repetidas que podem indicar um problema recorrente."""
        error_messages = [e.message for e in entries if e.level in {SeverityLevel.ERROR, SeverityLevel.CRITICAL}]
        counter: Counter[str] = Counter(error_messages)
        return [
            f"Mensagem repetida {count}x: {msg[:120]}"
            for msg, count in counter.most_common(5)
            if count > 2
        ]
