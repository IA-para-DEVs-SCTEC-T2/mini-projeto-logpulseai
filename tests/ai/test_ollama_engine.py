"""Testes para OllamaAIEngine e AIEngine.

Cobre interface abstrata, amostragem estratificada, disponibilidade,
timeout, retry, parsing de resposta e validação de schema.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import openai
import pytest
from pydantic import ValidationError

from src.ai.base import AIEngine
from src.ai.ollama_engine import (
    _MAX_RETRIES,
    _MAX_SAMPLE_ENTRIES,
    OllamaAIEngine,
    _filter_errors_only,
)
from src.exceptions import AIEngineTimeoutError, AIEngineUnavailableError
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    LogEntry,
    SeverityLevel,
)

# ---------------------------------------------------------------------------
# Helpers de fixture
# ---------------------------------------------------------------------------


def _make_entry(severity: SeverityLevel, message: str = "test log") -> LogEntry:
    """Cria uma LogEntry de teste com a severidade especificada."""
    return LogEntry(
        raw_content=message,
        severity=severity,
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        message=message,
    )


def _make_valid_diagnosis_json(n_hypotheses: int = 2) -> str:
    """Gera JSON válido de AIDiagnosis com n hipóteses (mínimo 2)."""
    hypotheses = [
        {
            "description": f"Hipótese {i + 1}",
            "probability": "alta" if i == 0 else "média" if i == 1 else "baixa",
            "action": f"Ação concreta {i + 1}",
            "related_line": None,
        }
        for i in range(n_hypotheses)
    ]
    data = {
        "summary": "Falha recorrente de conexão com banco de dados.",
        "probable_cause": "Pool de conexões esgotado.",
        "hypotheses": hypotheses,
        "suggested_fix": "Aumentar max_connections no pool.",
        "confidence": 0.85,
    }
    return json.dumps(data)


def _make_analysis_result() -> AnalysisResult:
    """Cria um AnalysisResult de teste."""
    return AnalysisResult(
        total_entries=10,
        error_count=5,
        warning_count=3,
        severity_distribution={SeverityLevel.ERROR: 5, SeverityLevel.WARNING: 3, SeverityLevel.INFO: 2},
    )


# ---------------------------------------------------------------------------
# Testes da interface abstrata AIEngine
# ---------------------------------------------------------------------------


class TestAIEngineInterface:
    """Testes para a interface abstrata AIEngine."""

    def test_cannot_instantiate_abstract(self) -> None:
        """AIEngine não pode ser instanciado diretamente."""
        with pytest.raises(TypeError):
            AIEngine()  # type: ignore[abstract]

    def test_ollama_engine_is_subclass(self) -> None:
        """OllamaAIEngine deve ser subclasse de AIEngine."""
        assert issubclass(OllamaAIEngine, AIEngine)

    def test_subclass_without_diagnose_raises(self) -> None:
        """Subclasse sem implementar diagnose deve lançar TypeError."""

        class IncompleteEngine(AIEngine):
            pass

        with pytest.raises(TypeError):
            IncompleteEngine()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Testes de filtragem de erros
# ---------------------------------------------------------------------------


class TestErrorFiltering:
    """Testes para a função de filtragem de erros."""

    def test_empty_entries_returns_empty(self) -> None:
        """Lista vazia retorna lista vazia."""
        assert _filter_errors_only([]) == []

    def test_entries_below_max_returned_as_is(self) -> None:
        """Menos de 10 erros retorna todos sem amostragem."""
        entries = [_make_entry(SeverityLevel.ERROR) for _ in range(5)]
        result = _filter_errors_only(entries)
        assert len(result) == 5

    def test_filtering_caps_at_10_entries(self) -> None:
        """Filtragem limita a 10 entradas no máximo."""
        entries = [_make_entry(SeverityLevel.ERROR) for _ in range(200)]
        result = _filter_errors_only(entries)
        assert len(result) <= _MAX_SAMPLE_ENTRIES

    def test_filters_only_errors_and_criticals(self) -> None:
        """Filtragem deve retornar apenas ERROR e CRITICAL."""
        errors = [_make_entry(SeverityLevel.ERROR) for _ in range(10)]
        criticals = [_make_entry(SeverityLevel.CRITICAL) for _ in range(5)]
        warnings = [_make_entry(SeverityLevel.WARNING) for _ in range(10)]
        infos = [_make_entry(SeverityLevel.INFO) for _ in range(10)]
        entries = errors + criticals + warnings + infos

        result = _filter_errors_only(entries, max_entries=20)

        # Deve ter apenas ERROR e CRITICAL
        assert all(e.severity in {SeverityLevel.ERROR, SeverityLevel.CRITICAL} for e in result)
        assert len(result) == 15  # 10 errors + 5 criticals

    def test_filtering_with_no_errors_returns_empty(self) -> None:
        """Filtragem retorna vazio quando não há erros."""
        entries = [_make_entry(SeverityLevel.INFO) for _ in range(100)]
        result = _filter_errors_only(entries)
        assert len(result) == 0

    def test_filtering_exact_max_entries(self) -> None:
        """Filtragem retorna exatamente max_entries quando há erros suficientes."""
        entries = [_make_entry(SeverityLevel.ERROR) for _ in range(100)]
        result = _filter_errors_only(entries, max_entries=10)
        assert len(result) == 10


# ---------------------------------------------------------------------------
# Testes de disponibilidade do Ollama
# ---------------------------------------------------------------------------


class TestOllamaAvailability:
    """Testes para verificação de disponibilidade do Ollama."""

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_unavailable_raises_error(self, mock_check: MagicMock) -> None:
        """AIEngineUnavailableError é lançado quando Ollama está indisponível."""
        mock_check.side_effect = AIEngineUnavailableError(
            "Ollama não está disponível em http://localhost:11434. Execute: ollama serve"
        )
        
        engine = OllamaAIEngine()
        with pytest.raises(AIEngineUnavailableError) as exc_info:
            engine.diagnose(_make_analysis_result(), [])

        assert "ollama" in str(exc_info.value).lower()

    @patch("src.ai.ollama_engine._check_ollama_availability")
    @patch("openai.OpenAI")
    def test_available_proceeds_to_call(
        self, mock_openai_class: MagicMock, mock_check: MagicMock
    ) -> None:
        """Quando Ollama está disponível, prossegue para chamada ao LLM."""
        mock_check.return_value = None  # Disponível

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json()
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        result = engine.diagnose(_make_analysis_result(), [])
        assert isinstance(result, AIDiagnosis)

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_unavailable_error_message_contains_ollama_serve(self, mock_check: MagicMock) -> None:
        """Mensagem de erro deve orientar o usuário a executar 'ollama serve'."""
        mock_check.side_effect = AIEngineUnavailableError(
            "Ollama não está disponível em http://localhost:11434. Execute: ollama serve"
        )

        engine = OllamaAIEngine()
        with pytest.raises(AIEngineUnavailableError) as exc_info:
            engine.diagnose(_make_analysis_result(), [])

        assert "ollama serve" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Testes de timeout e retry
# ---------------------------------------------------------------------------


class TestTimeoutAndRetry:
    """Testes para timeout e retry com backoff exponencial."""

    @patch("src.ai.ollama_engine._check_ollama_availability")
    @patch("src.ai.ollama_engine.time.sleep")
    def test_timeout_raises_after_2_attempts(
        self, mock_sleep: MagicMock, mock_check: MagicMock
    ) -> None:
        """AIEngineTimeoutError é lançado após 2 tentativas falhadas."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
            request=MagicMock()
        )

        engine = OllamaAIEngine()
        engine._client = mock_client

        with pytest.raises(AIEngineTimeoutError):
            engine.diagnose(_make_analysis_result(), [])

    @patch("src.ai.ollama_engine._check_ollama_availability")
    @patch("src.ai.ollama_engine.time.sleep")
    def test_retry_happens_2_times(
        self, mock_sleep: MagicMock, mock_check: MagicMock
    ) -> None:
        """O cliente deve ser chamado exatamente 2 vezes antes de desistir."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
            request=MagicMock()
        )

        engine = OllamaAIEngine()
        engine._client = mock_client

        with pytest.raises(AIEngineTimeoutError):
            engine.diagnose(_make_analysis_result(), [])

        assert mock_client.chat.completions.create.call_count == _MAX_RETRIES

    @patch("src.ai.ollama_engine._check_ollama_availability")
    @patch("src.ai.ollama_engine.time.sleep")
    def test_backoff_delays_are_correct(
        self, mock_sleep: MagicMock, mock_check: MagicMock
    ) -> None:
        """Backoff exponencial deve usar delay de 1s (antes da tentativa 2)."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
            request=MagicMock()
        )

        engine = OllamaAIEngine()
        engine._client = mock_client

        with pytest.raises(AIEngineTimeoutError):
            engine.diagnose(_make_analysis_result(), [])

        # Deve ter dormido 1 vez (entre tentativas 1→2)
        assert mock_sleep.call_count == 1
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1]

    @patch("src.ai.ollama_engine._check_ollama_availability")
    @patch("src.ai.ollama_engine.time.sleep")
    def test_connection_error_also_retries(
        self, mock_sleep: MagicMock, mock_check: MagicMock
    ) -> None:
        """APIConnectionError também deve acionar retry."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APIConnectionError(
            request=MagicMock()
        )

        engine = OllamaAIEngine()
        engine._client = mock_client

        with pytest.raises(AIEngineTimeoutError):
            engine.diagnose(_make_analysis_result(), [])

        assert mock_client.chat.completions.create.call_count == _MAX_RETRIES


# ---------------------------------------------------------------------------
# Testes de parsing e validação de resposta
# ---------------------------------------------------------------------------


class TestResponseParsing:
    """Testes para parsing e validação da resposta do LLM."""

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_valid_response_parsed_to_ai_diagnosis(self, mock_check: MagicMock) -> None:
        """Resposta válida é parseada corretamente para AIDiagnosis."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json(3)
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        result = engine.diagnose(_make_analysis_result(), [])

        assert isinstance(result, AIDiagnosis)
        assert result.summary == "Falha recorrente de conexão com banco de dados."
        assert result.probable_cause == "Pool de conexões esgotado."
        assert len(result.hypotheses) == 3

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_diagnosis_has_at_least_2_hypotheses(self, mock_check: MagicMock) -> None:
        """Diagnóstico válido deve ter pelo menos 2 hipóteses."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json(5)
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        result = engine.diagnose(_make_analysis_result(), [])

        assert len(result.hypotheses) >= 2

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_response_with_less_than_2_hypotheses_raises_validation_error(
        self, mock_check: MagicMock
    ) -> None:
        """Resposta com menos de 2 hipóteses deve lançar ValidationError."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json(1)  # Apenas 1 hipótese
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        with pytest.raises(ValidationError):
            engine.diagnose(_make_analysis_result(), [])

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_response_with_empty_action_raises_validation_error(
        self, mock_check: MagicMock
    ) -> None:
        """Resposta com action vazio em hipótese deve lançar ValidationError."""
        mock_check.return_value = None

        invalid_json = json.dumps({
            "summary": "Problema detectado.",
            "probable_cause": "Causa desconhecida.",
            "hypotheses": [
                {"description": "H1", "probability": "alta", "action": "Ação 1"},
                {"description": "H2", "probability": "média", "action": "Ação 2"},
                {"description": "H3", "probability": "baixa", "action": ""},  # action vazio
            ],
            "suggested_fix": "",
            "confidence": 0.5,
        })

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = invalid_json
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        with pytest.raises(ValidationError):
            engine.diagnose(_make_analysis_result(), [])

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_response_with_markdown_code_block_is_parsed(self, mock_check: MagicMock) -> None:
        """Resposta com bloco de código markdown deve ser parseada corretamente."""
        mock_check.return_value = None

        json_content = _make_valid_diagnosis_json(3)
        markdown_wrapped = f"```json\n{json_content}\n```"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = markdown_wrapped
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        result = engine.diagnose(_make_analysis_result(), [])
        assert isinstance(result, AIDiagnosis)

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_each_hypothesis_has_non_empty_action(self, mock_check: MagicMock) -> None:
        """Cada hipótese no diagnóstico deve ter action não vazio."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json(4)
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        result = engine.diagnose(_make_analysis_result(), [])

        for hypothesis in result.hypotheses:
            assert hypothesis.action.strip() != ""


# ---------------------------------------------------------------------------
# Testes de integração do fluxo completo
# ---------------------------------------------------------------------------


class TestOllamaEngineIntegration:
    """Testes de integração do fluxo completo do OllamaAIEngine."""

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_diagnose_with_sample_entries(self, mock_check: MagicMock) -> None:
        """diagnose funciona com entradas de amostra reais."""
        mock_check.return_value = None

        entries = (
            [_make_entry(SeverityLevel.ERROR, "Database connection failed") for _ in range(10)]
            + [_make_entry(SeverityLevel.WARNING, "Slow query detected") for _ in range(5)]
            + [_make_entry(SeverityLevel.INFO, "Request processed") for _ in range(5)]
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json(3)
        mock_client.chat.completions.create.return_value = mock_response

        engine = OllamaAIEngine()
        engine._client = mock_client

        result = engine.diagnose(_make_analysis_result(), entries)

        assert isinstance(result, AIDiagnosis)
        assert len(result.hypotheses) >= 2

    @patch("src.ai.ollama_engine._check_ollama_availability")
    def test_diagnose_succeeds_on_second_attempt(self, mock_check: MagicMock) -> None:
        """diagnose deve ter sucesso na segunda tentativa após falha na primeira."""
        mock_check.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = _make_valid_diagnosis_json(2)

        # Falha na primeira tentativa, sucesso na segunda
        mock_client.chat.completions.create.side_effect = [
            openai.APITimeoutError(request=MagicMock()),
            mock_response,
        ]

        engine = OllamaAIEngine()
        engine._client = mock_client

        with patch("src.ai.ollama_engine.time.sleep"):
            result = engine.diagnose(_make_analysis_result(), [])

        assert isinstance(result, AIDiagnosis)
        assert mock_client.chat.completions.create.call_count == 2
