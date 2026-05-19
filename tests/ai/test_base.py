"""Testes unitários para a interface abstrata AIEngine.

Valida o contrato abstrato que toda implementação de AI engine
deve respeitar (RF-05.1).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.ai.base import AIEngine
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogEntry,
    SeverityLevel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_analysis() -> AnalysisResult:
    """Cria um AnalysisResult mínimo para testes."""
    return AnalysisResult(
        total_entries=5,
        error_count=2,
        warning_count=1,
    )


def _make_entries(n: int = 3) -> list[LogEntry]:
    """Cria lista de LogEntry para testes."""
    return [
        LogEntry(
            raw_content=f"ERROR: test message {i}",
            severity=SeverityLevel.ERROR,
            timestamp=datetime(2024, 1, 15, 10, 0, i, tzinfo=UTC),
        )
        for i in range(n)
    ]


def _make_diagnosis() -> AIDiagnosis:
    """Cria um AIDiagnosis válido para testes."""
    return AIDiagnosis(
        summary="Problema de conexão com banco de dados",
        probable_cause="Pool de conexões esgotado",
        hypotheses=[
            Hypothesis(description="H1", probability="alta", action="Verificar pool"),
            Hypothesis(description="H2", probability="média", action="Reiniciar serviço"),
            Hypothesis(description="H3", probability="baixa", action="Verificar rede"),
        ],
        suggested_fix="Aumentar max_connections",
        confidence=0.85,
    )


# ===========================================================================
# Testes da interface abstrata
# ===========================================================================


class TestAIEngineContract:
    """Valida que AIEngine define o contrato abstrato corretamente."""

    def test_cannot_instantiate_directly(self) -> None:
        """AIEngine não pode ser instanciado diretamente (é abstrato)."""
        with pytest.raises(TypeError):
            AIEngine()  # type: ignore[abstract]

    def test_requires_diagnose_method(self) -> None:
        """Subclasse sem implementar diagnose lança TypeError."""

        class IncompleteEngine(AIEngine):
            pass

        with pytest.raises(TypeError):
            IncompleteEngine()  # type: ignore[abstract]

    def test_concrete_subclass_can_be_instantiated(self) -> None:
        """Subclasse que implementa diagnose pode ser instanciada."""

        class ConcreteEngine(AIEngine):
            def diagnose(
                self,
                analysis: AnalysisResult,
                sample_entries: list[LogEntry],
            ) -> AIDiagnosis:
                return _make_diagnosis()

        engine = ConcreteEngine()
        assert isinstance(engine, AIEngine)

    def test_diagnose_signature_accepts_analysis_and_entries(self) -> None:
        """diagnose aceita AnalysisResult e List[LogEntry] como parâmetros."""

        class ConcreteEngine(AIEngine):
            def diagnose(
                self,
                analysis: AnalysisResult,
                sample_entries: list[LogEntry],
            ) -> AIDiagnosis:
                return _make_diagnosis()

        engine = ConcreteEngine()
        result = engine.diagnose(_make_analysis(), _make_entries())
        assert isinstance(result, AIDiagnosis)

    def test_diagnose_returns_ai_diagnosis(self) -> None:
        """diagnose deve retornar um AIDiagnosis válido."""

        class ConcreteEngine(AIEngine):
            def diagnose(
                self,
                analysis: AnalysisResult,
                sample_entries: list[LogEntry],
            ) -> AIDiagnosis:
                return _make_diagnosis()

        engine = ConcreteEngine()
        result = engine.diagnose(_make_analysis(), _make_entries())

        assert isinstance(result, AIDiagnosis)
        assert result.summary != ""
        assert result.probable_cause != ""
        assert len(result.hypotheses) >= 3

    def test_diagnose_with_empty_entries(self) -> None:
        """diagnose deve funcionar com lista vazia de entradas."""

        class ConcreteEngine(AIEngine):
            def diagnose(
                self,
                analysis: AnalysisResult,
                sample_entries: list[LogEntry],
            ) -> AIDiagnosis:
                return _make_diagnosis()

        engine = ConcreteEngine()
        result = engine.diagnose(_make_analysis(), [])
        assert isinstance(result, AIDiagnosis)

    def test_is_abstract_base_class(self) -> None:
        """AIEngine herda de ABC."""
        from abc import ABC

        assert issubclass(AIEngine, ABC)

    def test_diagnose_is_abstract_method(self) -> None:
        """diagnose é marcado como abstractmethod."""
        assert getattr(AIEngine.diagnose, "__isabstractmethod__", False)
