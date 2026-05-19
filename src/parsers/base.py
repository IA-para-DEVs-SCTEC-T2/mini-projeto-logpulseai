"""Interface abstrata para parsers de log do LogPulse IA."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.schemas import LogEntry, LogTemplate


class LogParser(ABC):
    """Interface abstrata para implementações de parser de log.

    Todo parser concreto deve implementar os métodos `parse` e
    `get_templates`, garantindo que o contrato seja respeitado
    independentemente do formato de log suportado.
    """

    @abstractmethod
    def parse(self, raw_content: str) -> list[LogEntry]:
        """Transforma conteúdo bruto de log em lista de LogEntry.

        Args:
            raw_content: Conteúdo bruto do arquivo ou texto de log.

        Returns:
            Lista de entradas de log normalizadas. Linhas malformadas
            são ignoradas sem interromper o processamento.
        """
        ...

    @abstractmethod
    def get_templates(self) -> list[LogTemplate]:
        """Retorna os templates extraídos pelo Drain3 até o momento.

        Returns:
            Lista de templates com padrão, contagem e amostras.
        """
        ...
