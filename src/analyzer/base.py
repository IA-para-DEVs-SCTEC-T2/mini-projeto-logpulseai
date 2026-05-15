"""Interface abstrata para analyzers de log do LogPulse IA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.models.schemas import AnalysisResult, LogEntry, LogTemplate


class LogAnalyzer(ABC):
    """Interface abstrata para implementações de analyzer de log.

    Todo analyzer concreto deve implementar o método `analyze`,
    garantindo que o contrato seja respeitado independentemente
    da estratégia de detecção de anomalias utilizada.
    """

    @abstractmethod

    def analyze(self, entries: List[LogEntry], templates: List[LogTemplate]) -> AnalysisResult:
        """Analisa um stream de logs e detecta anomalias.

        Args:
            entries: Lista de entradas de log normalizadas pelo parser.
            templates: Lista de templates extraídos pelo Drain3.

        Returns:
            AnalysisResult contendo anomalias detectadas, distribuição
            de severidade, spikes e metadados da análise.

        Note:
            Se entries contiver menos de 2 entradas, o resultado
            deve ter insufficient_data=True e não executar detecção
            de anomalias.
=======
    def analyze(
        self,
        entries: List[LogEntry],
        templates: List[LogTemplate],
    ) -> AnalysisResult:
        """Analisa um conjunto de entradas de log e detecta anomalias.

        Args:
            entries: Lista de entradas de log normalizadas.
            templates: Templates extraídos pelo parser (Drain3).

        Returns:
            Resultado da análise contendo distribuição de severidade,
            spikes detectados, stack traces agrupados e metadados.
        """
        ...
