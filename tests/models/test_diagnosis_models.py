"""Testes unitários e de propriedade para modelos de diagnóstico IA (Hypothesis, AIDiagnosis).

Valida os requisitos RF-05.2 e RF-05.3:
- Hypothesis: hipótese de causa raiz com probabilidade e ação
- AIDiagnosis: diagnóstico completo com resumo, causa e hipóteses
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.schemas import AIDiagnosis, Hypothesis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_hypothesis(**kwargs: object) -> Hypothesis:
    """Cria Hypothesis com defaults válidos."""
    defaults: dict[str, object] = {
        "description": "Conexão com banco de dados falhou",
        "probability": "alta",
        "action": "Verificar string de conexão e disponibilidade do banco",
    }
    defaults.update(kwargs)
    return Hypothesis(**defaults)  # type: ignore[arg-type]


def _make_diagnosis(**kwargs: object) -> AIDiagnosis:
    """Cria AIDiagnosis com defaults válidos."""
    defaults: dict[str, object] = {
        "summary": "Falha de conexão com banco de dados",
        "probable_cause": "Banco de dados indisponível",
        "hypotheses": [
            _make_hypothesis(description="Causa 1", probability="alta"),
            _make_hypothesis(description="Causa 2", probability="média"),
            _make_hypothesis(description="Causa 3", probability="baixa"),
        ],
    }
    defaults.update(kwargs)
    return AIDiagnosis(**defaults)  # type: ignore[arg-type]


# ===========================================================================
# Hypothesis — Testes unitários
# ===========================================================================


class TestHypothesisModel:
    """Testes para o modelo Hypothesis."""

    def test_valid_hypothesis(self) -> None:
        """Hypothesis válida com todos os campos."""
        h = _make_hypothesis()
        assert h.description == "Conexão com banco de dados falhou"
        assert h.probability == "alta"
        assert h.action == "Verificar string de conexão e disponibilidade do banco"
        assert h.related_line is None

    def test_probability_alta(self) -> None:
        """probability 'alta' é aceita."""
        h = _make_hypothesis(probability="alta")
        assert h.probability == "alta"

    def test_probability_media(self) -> None:
        """probability 'média' é aceita."""
        h = _make_hypothesis(probability="média")
        assert h.probability == "média"

    def test_probability_baixa(self) -> None:
        """probability 'baixa' é aceita."""
        h = _make_hypothesis(probability="baixa")
        assert h.probability == "baixa"

    def test_probability_case_insensitive(self) -> None:
        """probability é normalizada para lowercase."""
        h = _make_hypothesis(probability="ALTA")
        assert h.probability == "alta"

    def test_probability_mixed_case(self) -> None:
        """probability com case misto é normalizada."""
        h = _make_hypothesis(probability="Média")
        assert h.probability == "média"

    def test_invalid_probability_raises(self) -> None:
        """probability inválida lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_hypothesis(probability="high")

    def test_invalid_probability_english(self) -> None:
        """probability em inglês é rejeitada."""
        for prob in ("high", "medium", "low"):
            with pytest.raises(ValidationError):
                _make_hypothesis(probability=prob)

    def test_empty_description_raises(self) -> None:
        """description vazia lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_hypothesis(description="")

    def test_empty_action_raises(self) -> None:
        """action vazia lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_hypothesis(action="")

    def test_blank_action_raises(self) -> None:
        """action com apenas espaços lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_hypothesis(action="   ")

    def test_related_line_optional(self) -> None:
        """related_line é opcional (None por default)."""
        h = _make_hypothesis()
        assert h.related_line is None

    def test_related_line_accepts_int(self) -> None:
        """related_line aceita inteiro."""
        h = _make_hypothesis(related_line=42)
        assert h.related_line == 42

    def test_hypothesis_serialization(self) -> None:
        """Hypothesis pode ser serializada para dict."""
        h = _make_hypothesis(related_line=10)
        data = h.model_dump()
        assert data["probability"] == "alta"
        assert data["related_line"] == 10

    def test_hypothesis_json_roundtrip(self) -> None:
        """Hypothesis pode ser serializada e deserializada via JSON."""
        h = _make_hypothesis(related_line=5)
        json_str = h.model_dump_json()
        restored = Hypothesis.model_validate_json(json_str)
        assert restored.description == h.description
        assert restored.probability == h.probability
        assert restored.related_line == 5


# ===========================================================================
# AIDiagnosis — Testes unitários
# ===========================================================================


class TestAIDiagnosisModel:
    """Testes para o modelo AIDiagnosis."""

    def test_valid_diagnosis(self) -> None:
        """AIDiagnosis válido com campos obrigatórios."""
        diag = _make_diagnosis()
        assert diag.summary == "Falha de conexão com banco de dados"
        assert diag.probable_cause == "Banco de dados indisponível"
        assert len(diag.hypotheses) == 3

    def test_minimum_3_hypotheses_required(self) -> None:
        """AIDiagnosis requer mínimo de 3 hipóteses."""
        with pytest.raises(ValidationError):
            _make_diagnosis(
                hypotheses=[
                    _make_hypothesis(description="H1"),
                    _make_hypothesis(description="H2"),
                ]
            )

    def test_exactly_3_hypotheses_accepted(self) -> None:
        """Exatamente 3 hipóteses é aceito."""
        diag = _make_diagnosis()
        assert len(diag.hypotheses) == 3

    def test_more_than_3_hypotheses_accepted(self) -> None:
        """Mais de 3 hipóteses é aceito."""
        diag = _make_diagnosis(
            hypotheses=[_make_hypothesis(description=f"H{i}") for i in range(7)]
        )
        assert len(diag.hypotheses) == 7

    def test_empty_summary_raises(self) -> None:
        """summary vazio lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_diagnosis(summary="")

    def test_empty_probable_cause_raises(self) -> None:
        """probable_cause vazio lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_diagnosis(probable_cause="")

    def test_confidence_default_zero(self) -> None:
        """confidence tem default 0.0."""
        diag = _make_diagnosis()
        assert diag.confidence == 0.0

    def test_confidence_valid_range(self) -> None:
        """confidence aceita valores entre 0.0 e 1.0."""
        diag = _make_diagnosis(confidence=0.85)
        assert diag.confidence == 0.85

    def test_confidence_zero_accepted(self) -> None:
        """confidence = 0.0 é aceito."""
        diag = _make_diagnosis(confidence=0.0)
        assert diag.confidence == 0.0

    def test_confidence_one_accepted(self) -> None:
        """confidence = 1.0 é aceito."""
        diag = _make_diagnosis(confidence=1.0)
        assert diag.confidence == 1.0

    def test_confidence_above_one_raises(self) -> None:
        """confidence > 1.0 lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_diagnosis(confidence=1.1)

    def test_confidence_below_zero_raises(self) -> None:
        """confidence < 0.0 lança ValidationError."""
        with pytest.raises(ValidationError):
            _make_diagnosis(confidence=-0.1)

    def test_suggested_fix_default_empty(self) -> None:
        """suggested_fix tem default de string vazia."""
        diag = _make_diagnosis()
        assert diag.suggested_fix == ""

    def test_suggested_fix_accepts_text(self) -> None:
        """suggested_fix aceita texto."""
        diag = _make_diagnosis(suggested_fix="Reiniciar o serviço de banco de dados")
        assert diag.suggested_fix == "Reiniciar o serviço de banco de dados"

    def test_diagnosis_serialization(self) -> None:
        """AIDiagnosis pode ser serializado para dict."""
        diag = _make_diagnosis(confidence=0.9)
        data = diag.model_dump()
        assert data["confidence"] == 0.9
        assert len(data["hypotheses"]) == 3

    def test_diagnosis_json_roundtrip(self) -> None:
        """AIDiagnosis pode ser serializado e deserializado via JSON."""
        diag = _make_diagnosis(confidence=0.75, suggested_fix="Aumentar pool")
        json_str = diag.model_dump_json()
        restored = AIDiagnosis.model_validate_json(json_str)
        assert restored.summary == diag.summary
        assert restored.confidence == 0.75
        assert len(restored.hypotheses) == 3

    def test_hypotheses_ordered_by_probability(self) -> None:
        """Hipóteses podem ser ordenadas por probabilidade."""
        diag = _make_diagnosis()
        probs = [h.probability for h in diag.hypotheses]
        assert probs == ["alta", "média", "baixa"]


# ===========================================================================
# Property-Based Tests — Hypothesis
# ===========================================================================


@given(prob=st.sampled_from(["alta", "média", "baixa"]))
@settings(max_examples=20)
def test_hypothesis_valid_probabilities_always_accepted(prob: str) -> None:
    """Propriedade: probabilidades válidas são sempre aceitas."""
    h = _make_hypothesis(probability=prob)
    assert h.probability == prob


@given(
    desc=st.text(min_size=1, max_size=200),
    action=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
)
@settings(max_examples=50)
def test_hypothesis_any_non_empty_desc_and_action_accepted(
    desc: str, action: str
) -> None:
    """Propriedade: description e action não vazios são sempre aceitos."""
    h = Hypothesis(
        description=desc,
        probability="alta",
        action=action,
    )
    assert h.description == desc


@given(prob=st.text(min_size=1, max_size=20).filter(lambda x: x.strip().lower() not in {"alta", "média", "baixa"}))
@settings(max_examples=30)
def test_hypothesis_invalid_probability_always_rejected(prob: str) -> None:
    """Propriedade: probabilidades inválidas são sempre rejeitadas."""
    with pytest.raises(ValidationError):
        _make_hypothesis(probability=prob)


# ===========================================================================
# Property-Based Tests — AIDiagnosis
# ===========================================================================


@given(confidence=st.floats(min_value=0.0, max_value=1.0))
@settings(max_examples=50)
def test_diagnosis_confidence_in_range_always_accepted(confidence: float) -> None:
    """Propriedade: confidence entre 0.0 e 1.0 é sempre aceito."""
    diag = _make_diagnosis(confidence=confidence)
    assert 0.0 <= diag.confidence <= 1.0


@given(confidence=st.floats(min_value=1.01, max_value=100.0))
@settings(max_examples=20)
def test_diagnosis_confidence_above_one_always_rejected(confidence: float) -> None:
    """Propriedade: confidence > 1.0 é sempre rejeitado."""
    with pytest.raises(ValidationError):
        _make_diagnosis(confidence=confidence)


@given(n=st.integers(min_value=3, max_value=10))
@settings(max_examples=20)
def test_diagnosis_accepts_3_or_more_hypotheses(n: int) -> None:
    """Propriedade: 3 ou mais hipóteses são sempre aceitas."""
    hypotheses = [_make_hypothesis(description=f"H{i}") for i in range(n)]
    diag = _make_diagnosis(hypotheses=hypotheses)
    assert len(diag.hypotheses) == n


@given(n=st.integers(min_value=0, max_value=2))
@settings(max_examples=10)
def test_diagnosis_rejects_less_than_3_hypotheses(n: int) -> None:
    """Propriedade: menos de 3 hipóteses é sempre rejeitado."""
    hypotheses = [_make_hypothesis(description=f"H{i}") for i in range(n)]
    with pytest.raises(ValidationError):
        _make_diagnosis(hypotheses=hypotheses)
