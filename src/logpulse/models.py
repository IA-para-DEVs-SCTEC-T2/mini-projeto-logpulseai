"""Modelos de dados centrais do LogPulse IA."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Nível de severidade de uma entrada de log."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Representa uma entrada de log estruturada e normalizada."""

    timestamp: datetime
    level: SeverityLevel
    message: str
    source: str
    raw: str | None = None
    timestamp_inferred: bool = False
    level_inferred: bool = False
    extra: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Valida os campos obrigatórios após inicialização."""
        if not self.message:
            raise ValueError("O campo 'message' não pode ser vazio.")
        if not self.source:
            raise ValueError("O campo 'source' não pode ser vazio.")
        if self.timestamp.tzinfo is None:
            raise ValueError("O campo 'timestamp' deve conter timezone.")


@dataclass
class AnalysisResult:
    """Resultado da análise de um conjunto de entradas de log."""

    total_entries: int
    error_count: int
    warning_count: int
    anomalies: list[str] = field(default_factory=list)
    spikes: list[str] = field(default_factory=list)
    summary: str = ""
