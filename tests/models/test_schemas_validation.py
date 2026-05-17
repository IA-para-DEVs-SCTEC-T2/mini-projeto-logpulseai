"""Testes de validação de schemas Pydantic.

Valida que todos os schemas Pydantic estão validando corretamente:
- Campos obrigatórios
- Validações de tipo
- Validações de tamanho (max_length, ge, le)
- Validações customizadas (validators)
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogEntry,
    LogFileUpload,
    LogListParams,
    LogTemplate,
    LogTextUpload,
    SeverityLevel,
    Spike,
)


# ============================================================================
# Testes de SeverityLevel (Enum)
# ============================================================================


class TestSeverityLevel:
    """Testes para o enum SeverityLevel."""

    def test_severity_level_valid_values(self) -> None:
        """Enum aceita apenas valores válidos."""
        assert SeverityLevel.DEBUG == "DEBUG"
        assert SeverityLevel.INFO == "INFO"
        assert SeverityLevel.WARNING == "WARNING"
        assert SeverityLevel.ERROR == "ERROR"
        assert SeverityLevel.CRITICAL == "CRITICAL"

    def test_severity_level_invalid_value(self) -> None:
        """Enum rejeita valores inválidos."""
        with pytest.raises(ValueError):
            SeverityLevel("INVALID")  # type: ignore


# ============================================================================
# Testes de LogEntry
# ============================================================================


class TestLogEntry:
    """Testes para o modelo LogEntry."""

    def test_log_entry_valid(self) -> None:
        """LogEntry aceita dados válidos."""
        entry = LogEntry(
            raw_content="2024-01-15 10:00:00 ERROR Database connection failed",
            severity=SeverityLevel.ERROR,
            message="Database connection failed",
        )
        assert entry.raw_content == "2024-01-15 10:00:00 ERROR Database connection failed"
        assert entry.severity == SeverityLevel.ERROR
        assert entry.message == "Database connection failed"
        assert entry.level_inferred is False
        assert entry.timestamp_inferred is False

    def test_log_entry_required_field_missing(self) -> None:
        """LogEntry rejeita quando campo obrigatório está ausente."""
        with pytest.raises(ValidationError) as exc_info:
            LogEntry()  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("raw_content",) for e in errors)

    def test_log_entry_empty_raw_content(self) -> None:
        """LogEntry rejeita raw_content vazio."""
        with pytest.raises(ValidationError) as exc_info:
            LogEntry(raw_content="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("raw_content",) for e in errors)

    def test_log_entry_strips_whitespace(self) -> None:
        """LogEntry remove espaços em branco do raw_content."""
        entry = LogEntry(raw_content="  test content  ")
        assert entry.raw_content == "test content"

    def test_log_entry_default_severity(self) -> None:
        """LogEntry usa INFO como severidade padrão."""
        entry = LogEntry(raw_content="test")
        assert entry.severity == SeverityLevel.INFO

    def test_log_entry_inference_flags(self) -> None:
        """LogEntry permite marcar campos inferidos."""
        entry = LogEntry(
            raw_content="test",
            level_inferred=True,
            timestamp_inferred=True,
        )
        assert entry.level_inferred is True
        assert entry.timestamp_inferred is True


# ============================================================================
# Testes de LogTemplate
# ============================================================================


class TestLogTemplate:
    """Testes para o modelo LogTemplate."""

    def test_log_template_valid(self) -> None:
        """LogTemplate aceita dados válidos."""
        template = LogTemplate(
            template_id="template-1",
            pattern="Database timeout <*>",
            occurrences=10,
            sample_messages=["Database timeout 30s", "Database timeout 45s"],
        )
        assert template.template_id == "template-1"
        assert template.pattern == "Database timeout <*>"
        assert template.occurrences == 10
        assert len(template.sample_messages) == 2

    def test_log_template_limits_samples_to_5(self) -> None:
        """LogTemplate limita sample_messages a 5 itens."""
        template = LogTemplate(
            template_id="template-1",
            pattern="Test <*>",
            sample_messages=["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7"],
        )
        assert len(template.sample_messages) == 5
        assert template.sample_messages == ["msg1", "msg2", "msg3", "msg4", "msg5"]

    def test_log_template_occurrences_non_negative(self) -> None:
        """LogTemplate rejeita occurrences negativo."""
        with pytest.raises(ValidationError) as exc_info:
            LogTemplate(
                template_id="template-1",
                pattern="Test",
                occurrences=-1,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("occurrences",) for e in errors)

    def test_log_template_required_fields(self) -> None:
        """LogTemplate rejeita quando campos obrigatórios estão ausentes."""
        with pytest.raises(ValidationError) as exc_info:
            LogTemplate()  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("template_id",) for e in errors)
        assert any(e["loc"] == ("pattern",) for e in errors)


# ============================================================================
# Testes de Spike
# ============================================================================


class TestSpike:
    """Testes para o modelo Spike."""

    def test_spike_valid(self) -> None:
        """Spike aceita dados válidos."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=60)
        spike = Spike(
            start_time=start,
            end_time=end,
            error_count=15,
            template_ids=["template-1", "template-2"],
        )
        assert spike.start_time == start
        assert spike.end_time == end
        assert spike.error_count == 15
        assert len(spike.template_ids) == 2

    def test_spike_validates_end_time_after_start_time(self) -> None:
        """Spike valida que end_time > start_time."""
        start = datetime.now(timezone.utc)
        end = start - timedelta(seconds=10)  # end antes de start
        with pytest.raises(ValidationError) as exc_info:
            Spike(start_time=start, end_time=end, error_count=10)
        assert "end_time deve ser posterior a start_time" in str(exc_info.value)

    def test_spike_validates_end_time_equal_start_time(self) -> None:
        """Spike rejeita end_time igual a start_time."""
        start = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            Spike(start_time=start, end_time=start, error_count=10)
        assert "end_time deve ser posterior a start_time" in str(exc_info.value)

    def test_spike_minimum_error_count(self) -> None:
        """Spike rejeita error_count < 10."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=60)
        with pytest.raises(ValidationError) as exc_info:
            Spike(start_time=start, end_time=end, error_count=9)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("error_count",) for e in errors)

    def test_spike_required_fields(self) -> None:
        """Spike rejeita quando campos obrigatórios estão ausentes."""
        with pytest.raises(ValidationError) as exc_info:
            Spike()  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("start_time",) for e in errors)
        assert any(e["loc"] == ("end_time",) for e in errors)
        assert any(e["loc"] == ("error_count",) for e in errors)


# ============================================================================
# Testes de AnalysisResult
# ============================================================================


class TestAnalysisResult:
    """Testes para o modelo AnalysisResult."""

    def test_analysis_result_valid(self) -> None:
        """AnalysisResult aceita dados válidos."""
        result = AnalysisResult(
            total_entries=100,
            severity_distribution={
                SeverityLevel.ERROR: 10,
                SeverityLevel.WARNING: 20,
                SeverityLevel.INFO: 70,
            },
            error_count=10,
            warning_count=20,
        )
        assert result.total_entries == 100
        assert result.error_count == 10
        assert result.warning_count == 20
        assert result.insufficient_data is False

    def test_analysis_result_non_negative_counters(self) -> None:
        """AnalysisResult rejeita contadores negativos."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisResult(total_entries=-1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("total_entries",) for e in errors)

        with pytest.raises(ValidationError) as exc_info:
            AnalysisResult(error_count=-1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("error_count",) for e in errors)

        with pytest.raises(ValidationError) as exc_info:
            AnalysisResult(warning_count=-1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("warning_count",) for e in errors)

    def test_analysis_result_insufficient_data_flag(self) -> None:
        """AnalysisResult permite marcar dados insuficientes."""
        result = AnalysisResult(total_entries=1, insufficient_data=True)
        assert result.insufficient_data is True


# ============================================================================
# Testes de Hypothesis
# ============================================================================


class TestHypothesis:
    """Testes para o modelo Hypothesis."""

    def test_hypothesis_valid(self) -> None:
        """Hypothesis aceita dados válidos."""
        hyp = Hypothesis(
            description="Pool de conexões esgotado",
            probability="alta",
            action="Verificar configuração de max_connections",
            related_line=42,
        )
        assert hyp.description == "Pool de conexões esgotado"
        assert hyp.probability == "alta"
        assert hyp.action == "Verificar configuração de max_connections"
        assert hyp.related_line == 42

    def test_hypothesis_probability_validation(self) -> None:
        """Hypothesis aceita apenas 'alta', 'média' ou 'baixa'."""
        # Válidos
        for prob in ["alta", "média", "baixa"]:
            hyp = Hypothesis(description="test", probability=prob, action="test")
            assert hyp.probability == prob

        # Inválido
        with pytest.raises(ValidationError) as exc_info:
            Hypothesis(description="test", probability="muito alta", action="test")
        assert "probability deve ser 'alta', 'média' ou 'baixa'" in str(exc_info.value)

    def test_hypothesis_probability_case_insensitive(self) -> None:
        """Hypothesis normaliza probability para lowercase."""
        hyp = Hypothesis(description="test", probability="ALTA", action="test")
        assert hyp.probability == "alta"

        hyp = Hypothesis(description="test", probability="Média", action="test")
        assert hyp.probability == "média"

    def test_hypothesis_action_not_empty(self) -> None:
        """Hypothesis rejeita action vazio."""
        with pytest.raises(ValidationError) as exc_info:
            Hypothesis(description="test", probability="alta", action="")
        # Pydantic's min_length validation triggers before custom validator
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("action",) for e in errors)

    def test_hypothesis_action_not_blank(self) -> None:
        """Hypothesis rejeita action com apenas espaços."""
        with pytest.raises(ValidationError) as exc_info:
            Hypothesis(description="test", probability="alta", action="   ")
        assert "action não pode ser vazio" in str(exc_info.value)

    def test_hypothesis_related_line_optional(self) -> None:
        """Hypothesis aceita related_line None."""
        hyp = Hypothesis(description="test", probability="alta", action="test", related_line=None)
        assert hyp.related_line is None

    def test_hypothesis_required_fields(self) -> None:
        """Hypothesis rejeita quando campos obrigatórios estão ausentes."""
        with pytest.raises(ValidationError) as exc_info:
            Hypothesis()  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("description",) for e in errors)
        assert any(e["loc"] == ("probability",) for e in errors)
        assert any(e["loc"] == ("action",) for e in errors)


# ============================================================================
# Testes de AIDiagnosis
# ============================================================================


class TestAIDiagnosis:
    """Testes para o modelo AIDiagnosis."""

    def test_ai_diagnosis_valid(self) -> None:
        """AIDiagnosis aceita dados válidos."""
        diagnosis = AIDiagnosis(
            summary="Falha de conexão com banco de dados",
            probable_cause="Pool de conexões esgotado",
            hypotheses=[
                Hypothesis(description="Hipótese 1", probability="alta", action="Ação 1"),
                Hypothesis(description="Hipótese 2", probability="média", action="Ação 2"),
                Hypothesis(description="Hipótese 3", probability="baixa", action="Ação 3"),
            ],
        )
        assert diagnosis.summary == "Falha de conexão com banco de dados"
        assert diagnosis.probable_cause == "Pool de conexões esgotado"
        assert len(diagnosis.hypotheses) == 3

    def test_ai_diagnosis_minimum_3_hypotheses(self) -> None:
        """AIDiagnosis rejeita lista com < 3 hypotheses."""
        with pytest.raises(ValidationError) as exc_info:
            AIDiagnosis(
                summary="Test",
                probable_cause="Test",
                hypotheses=[
                    Hypothesis(description="H1", probability="alta", action="A1"),
                    Hypothesis(description="H2", probability="média", action="A2"),
                ],
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("hypotheses",) for e in errors)

    def test_ai_diagnosis_validates_hypothesis_actions(self) -> None:
        """AIDiagnosis valida que todas as hipóteses têm action não vazio."""
        with pytest.raises(ValidationError) as exc_info:
            AIDiagnosis(
                summary="Test",
                probable_cause="Test",
                hypotheses=[
                    Hypothesis(description="H1", probability="alta", action="A1"),
                    Hypothesis(description="H2", probability="média", action=""),  # action vazio
                    Hypothesis(description="H3", probability="baixa", action="A3"),
                ],
            )
        # O erro vem do validator do Hypothesis (min_length)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("action",) for e in errors)

    def test_ai_diagnosis_confidence_range(self) -> None:
        """AIDiagnosis valida que confidence está entre 0.0 e 1.0."""
        # Válido
        diagnosis = AIDiagnosis(
            summary="Test",
            probable_cause="Test",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="A1"),
                Hypothesis(description="H2", probability="média", action="A2"),
                Hypothesis(description="H3", probability="baixa", action="A3"),
            ],
            confidence=0.85,
        )
        assert diagnosis.confidence == 0.85

        # Inválido: < 0
        with pytest.raises(ValidationError) as exc_info:
            AIDiagnosis(
                summary="Test",
                probable_cause="Test",
                hypotheses=[
                    Hypothesis(description="H1", probability="alta", action="A1"),
                    Hypothesis(description="H2", probability="média", action="A2"),
                    Hypothesis(description="H3", probability="baixa", action="A3"),
                ],
                confidence=-0.1,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("confidence",) for e in errors)

        # Inválido: > 1
        with pytest.raises(ValidationError) as exc_info:
            AIDiagnosis(
                summary="Test",
                probable_cause="Test",
                hypotheses=[
                    Hypothesis(description="H1", probability="alta", action="A1"),
                    Hypothesis(description="H2", probability="média", action="A2"),
                    Hypothesis(description="H3", probability="baixa", action="A3"),
                ],
                confidence=1.5,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("confidence",) for e in errors)

    def test_ai_diagnosis_required_fields(self) -> None:
        """AIDiagnosis rejeita quando campos obrigatórios estão ausentes."""
        with pytest.raises(ValidationError) as exc_info:
            AIDiagnosis()  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("summary",) for e in errors)
        assert any(e["loc"] == ("probable_cause",) for e in errors)
        assert any(e["loc"] == ("hypotheses",) for e in errors)


# ============================================================================
# Testes de LogFileUpload
# ============================================================================


class TestLogFileUpload:
    """Testes para o schema LogFileUpload."""

    def test_log_file_upload_valid_log(self) -> None:
        """LogFileUpload aceita arquivo .log válido."""
        upload = LogFileUpload(
            filename="app.log",
            content="2024-01-15 10:00:00 ERROR Test error",
        )
        assert upload.filename == "app.log"
        assert upload.content == "2024-01-15 10:00:00 ERROR Test error"

    def test_log_file_upload_valid_txt(self) -> None:
        """LogFileUpload aceita arquivo .txt válido."""
        upload = LogFileUpload(
            filename="app.txt",
            content="Test content",
        )
        assert upload.filename == "app.txt"

    def test_log_file_upload_rejects_pdf(self) -> None:
        """LogFileUpload rejeita arquivo .pdf."""
        with pytest.raises(ValidationError) as exc_info:
            LogFileUpload(filename="document.pdf", content="test")
        assert "Apenas arquivos" in str(exc_info.value)

    def test_log_file_upload_rejects_docx(self) -> None:
        """LogFileUpload rejeita arquivo .docx."""
        with pytest.raises(ValidationError) as exc_info:
            LogFileUpload(filename="document.docx", content="test")
        assert "Apenas arquivos" in str(exc_info.value)

    def test_log_file_upload_case_insensitive_extension(self) -> None:
        """LogFileUpload aceita extensões em maiúsculas."""
        upload = LogFileUpload(filename="APP.LOG", content="test")
        assert upload.filename == "APP.LOG"

    def test_log_file_upload_max_size(self) -> None:
        """LogFileUpload rejeita arquivo > 50MB."""
        large_content = "x" * (50 * 1024 * 1024 + 1)  # 50MB + 1 char
        with pytest.raises(ValidationError) as exc_info:
            LogFileUpload(filename="large.log", content=large_content)
        assert "excede o limite de 50MB" in str(exc_info.value)

    def test_log_file_upload_empty_content(self) -> None:
        """LogFileUpload rejeita content vazio."""
        with pytest.raises(ValidationError) as exc_info:
            LogFileUpload(filename="app.log", content="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)


# ============================================================================
# Testes de LogTextUpload
# ============================================================================


class TestLogTextUpload:
    """Testes para o schema LogTextUpload."""

    def test_log_text_upload_valid(self) -> None:
        """LogTextUpload aceita texto válido."""
        upload = LogTextUpload(content="2024-01-15 10:00:00 ERROR Test error")
        assert upload.content == "2024-01-15 10:00:00 ERROR Test error"

    def test_log_text_upload_rejects_empty(self) -> None:
        """LogTextUpload rejeita content vazio."""
        with pytest.raises(ValidationError) as exc_info:
            LogTextUpload(content="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    def test_log_text_upload_max_length(self) -> None:
        """LogTextUpload rejeita content > 100.000 caracteres."""
        large_content = "x" * 100_001
        with pytest.raises(ValidationError) as exc_info:
            LogTextUpload(content=large_content)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    def test_log_text_upload_exactly_max_length(self) -> None:
        """LogTextUpload aceita content com exatamente 100.000 caracteres."""
        content = "x" * 100_000
        upload = LogTextUpload(content=content)
        assert len(upload.content) == 100_000

    def test_log_text_upload_required_field(self) -> None:
        """LogTextUpload rejeita quando content está ausente."""
        with pytest.raises(ValidationError) as exc_info:
            LogTextUpload()  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)


# ============================================================================
# Testes de LogListParams
# ============================================================================


class TestLogListParams:
    """Testes para o schema LogListParams."""

    def test_log_list_params_valid(self) -> None:
        """LogListParams aceita parâmetros válidos."""
        params = LogListParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50

    def test_log_list_params_defaults(self) -> None:
        """LogListParams usa valores padrão."""
        params = LogListParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_log_list_params_rejects_page_zero(self) -> None:
        """LogListParams rejeita page=0."""
        with pytest.raises(ValidationError) as exc_info:
            LogListParams(page=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page",) for e in errors)

    def test_log_list_params_rejects_negative_page(self) -> None:
        """LogListParams rejeita page negativo."""
        with pytest.raises(ValidationError) as exc_info:
            LogListParams(page=-1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page",) for e in errors)

    def test_log_list_params_rejects_page_size_over_100(self) -> None:
        """LogListParams rejeita page_size > 100."""
        with pytest.raises(ValidationError) as exc_info:
            LogListParams(page_size=101)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page_size",) for e in errors)

    def test_log_list_params_rejects_page_size_zero(self) -> None:
        """LogListParams rejeita page_size=0."""
        with pytest.raises(ValidationError) as exc_info:
            LogListParams(page_size=0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("page_size",) for e in errors)

    def test_log_list_params_accepts_page_size_100(self) -> None:
        """LogListParams aceita page_size=100 (limite máximo)."""
        params = LogListParams(page_size=100)
        assert params.page_size == 100


# ============================================================================
# Testes de tipos incorretos
# ============================================================================


class TestTypeValidation:
    """Testes para validação de tipos incorretos."""

    def test_log_entry_wrong_severity_type(self) -> None:
        """LogEntry rejeita severity com tipo incorreto."""
        with pytest.raises(ValidationError):
            LogEntry(raw_content="test", severity="INVALID")  # type: ignore

    def test_spike_wrong_datetime_type(self) -> None:
        """Spike rejeita datetime com tipo incorreto."""
        with pytest.raises(ValidationError):
            Spike(
                start_time="not a datetime",  # type: ignore
                end_time="not a datetime",  # type: ignore
                error_count=10,
            )

    def test_hypothesis_wrong_probability_type(self) -> None:
        """Hypothesis rejeita probability com tipo incorreto."""
        with pytest.raises(ValidationError):
            Hypothesis(
                description="test",
                probability=123,  # type: ignore
                action="test",
            )

    def test_analysis_result_wrong_dict_type(self) -> None:
        """AnalysisResult rejeita severity_distribution com tipo incorreto."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                severity_distribution="not a dict",  # type: ignore
            )
