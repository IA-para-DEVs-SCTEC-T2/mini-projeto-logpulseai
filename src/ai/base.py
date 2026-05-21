"""Interface abstrata para motores de IA do LogPulse IA."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.schemas import AIDiagnosis, AnalysisResult, LogEntry


class AIEngine(ABC):
    """Interface abstrata para implementações de motor de IA.

    Todo motor de IA concreto deve implementar o método `diagnose`,
    garantindo que o contrato seja respeitado independentemente do
    provedor de LLM utilizado (Ollama, OpenAI, Gemini, etc.).

    Example:
        >>> class MyEngine(AIEngine):
        ...     def diagnose(self, analysis, sample_entries):
        ...         return AIDiagnosis(...)
    """

    @abstractmethod
    def diagnose(
        self,
        analysis: AnalysisResult,
        sample_entries: list[LogEntry],
    ) -> AIDiagnosis:
        """Gera diagnóstico inteligente a partir da análise de logs.

        Args:
            analysis: Resultado da análise de anomalias contendo
                distribuição de severidade, spikes e stack traces.
            sample_entries: Amostra estratificada de entradas de log
                para contextualizar o diagnóstico.

        Returns:
            Diagnóstico estruturado com causa provável, hipóteses
            ordenadas por probabilidade e sugestão de correção.

        Raises:
            AIEngineTimeoutError: Se o LLM não responder dentro do timeout.
            AIEngineUnavailableError: Se o serviço de LLM estiver indisponível.
        """
        ...
