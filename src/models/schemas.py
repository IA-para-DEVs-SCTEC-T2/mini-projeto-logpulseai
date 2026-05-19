"""Schemas Pydantic para modelos de dados do LogPulse IA.

Define todos os modelos que representam logs, análises e diagnósticos,
além dos schemas de request/response da API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Dict, List, Optional



try:
    from typing import Annotated
except ImportError:
    from typing import Annotated

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================================
# Enums
# ============================================================================


class SeverityLevel(str, Enum):
    """Níveis de severidade de log suportados pelo sistema."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================================
# Modelos base de log
# ============================================================================


class LogEntry(BaseModel):
    """Representa uma entrada de log parseada e normalizada.

    Campos de inferência indicam quando o valor foi deduzido
    automaticamente (não estava presente no log original).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID único da entrada")
    raw_content: str = Field(..., min_length=1, description="Conteúdo bruto da linha de log")
    template_id: str | None = Field(default=None, description="ID do template Drain3 associado")
    severity: SeverityLevel = Field(default=SeverityLevel.INFO, description="Nível de severidade")
    timestamp: datetime | None = Field(default=None, description="Timestamp extraído do log")
    message: str = Field(default="", description="Mensagem principal do log")
    level_inferred: bool = Field(
        default=False, description="True se o nível foi inferido (não estava no log)"
    )
    timestamp_inferred: bool = Field(
        default=False, description="True se o timestamp foi inferido (não estava no log)"
    )

    model_config = {"str_strip_whitespace": True}

    @field_validator("raw_content", mode="before")
    @classmethod
    def clean_raw_content(cls, v: str) -> str:
        """Remove espaços em branco do início e fim."""
        if isinstance(v, str):
            v = v.strip()
        return v


class LogTemplate(BaseModel):
    """Template de log extraído pelo Drain3.

    Agrupa entradas de log com padrão similar, substituindo
    valores dinâmicos por placeholders.
    """

    template_id: str = Field(..., description="Identificador único do template")
    pattern: str = Field(..., description="Padrão do template com placeholders")
    occurrences: int = Field(default=0, ge=0, description="Número de ocorrências deste template")
    sample_messages: list[str] = Field(
        default_factory=list,
        description="Até 5 mensagens de exemplo deste template",
    )

    @field_validator("sample_messages")
    @classmethod
    def limit_samples(cls, v: list[str]) -> list[str]:
        """Garante no máximo 5 amostras por template."""
        return v[:5]


# ============================================================================
# Modelos de análise de anomalias
# ============================================================================


class Spike(BaseModel):
    """Representa um spike (pico) de erros detectado em uma janela de tempo.

    Um spike é caracterizado por 10 ou mais erros (ERROR/CRITICAL)
    em uma janela deslizante de 60 segundos.
    """

    start_time: datetime = Field(..., description="Início da janela do spike")
    end_time: datetime = Field(..., description="Fim da janela do spike")
    error_count: int = Field(..., ge=10, description="Número de erros no período (mínimo 10)")
    template_ids: list[str] = Field(
        default_factory=list, description="Templates de log envolvidos no spike"
    )

    @model_validator(mode="after")
    def validate_time_range(self) -> Spike:
        """Garante que end_time é posterior a start_time."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time deve ser posterior a start_time")
        return self


class AnalysisResult(BaseModel):
    """Resultado da análise de anomalias de um conjunto de logs.

    Contém distribuição de severidade, spikes detectados,
    stack traces agrupados e metadados da análise.
    """

    total_entries: int = Field(default=0, ge=0, description="Total de entradas analisadas")
    severity_distribution: dict[SeverityLevel, int] = Field(
        default_factory=dict, description="Contagem de entradas por nível de severidade"
    )
    error_count: int = Field(default=0, ge=0, description="Total de erros (ERROR + CRITICAL)")
    warning_count: int = Field(default=0, ge=0, description="Total de warnings")
    spikes: list[Spike] = Field(default_factory=list, description="Spikes de erro detectados")
    stack_traces: list[str] = Field(
        default_factory=list, description="Stack traces agrupados (Python, Java, Go)"
    )
    templates: list[LogTemplate] = Field(
        default_factory=list, description="Templates extraídos pelo Drain3"
    )
    insufficient_data: bool = Field(
        default=False, description="True se há menos de 2 entradas para análise confiável"
    )


# ============================================================================
# Modelos de diagnóstico IA
# ============================================================================

_VALID_PROBABILITIES = {"alta", "média", "baixa"}


class Hypothesis(BaseModel):
    """Hipótese de causa raiz gerada pela IA.

    Cada hipótese representa uma possível explicação para o problema
    identificado nos logs, com probabilidade estimada e ação sugerida.
    """

    description: str = Field(..., min_length=1, description="Descrição da hipótese de causa raiz")
    probability: str = Field(..., description="Probabilidade estimada: 'alta', 'média' ou 'baixa'")
    action: str = Field(..., min_length=1, description="Ação sugerida para investigar/corrigir")
    related_line: int | None = Field(
        default=None, description="Número da linha relacionada ao problema (opcional)"
    )

    @field_validator("probability")
    @classmethod
    def validate_probability(cls, v: str) -> str:
        """Aceita apenas 'alta', 'média' ou 'baixa'."""
        normalized = v.strip().lower()
        if normalized not in _VALID_PROBABILITIES:
            raise ValueError(f"probability deve ser 'alta', 'média' ou 'baixa'. Recebido: '{v}'")
        return normalized

    @field_validator("action")
    @classmethod
    def validate_action_not_blank(cls, v: str) -> str:
        """Garante que action não é apenas espaços em branco."""
        if not v.strip():
            raise ValueError("action não pode ser vazio ou apenas espaços")
        return v


class AIDiagnosis(BaseModel):
    """Diagnóstico completo gerado pela IA para um conjunto de logs.

    Contém resumo do problema, causa provável e lista de hipóteses
    ordenadas por probabilidade.
    """

    summary: str = Field(..., min_length=1, description="Resumo claro do problema identificado")
    probable_cause: str = Field(..., min_length=1, description="Causa raiz mais provável")
    hypotheses: Annotated[list[Hypothesis], Field(min_length=3)] = Field(
        ..., description="Lista de hipóteses (mínimo 3)"
    )
    suggested_fix: str = Field(default="", description="Sugestão de correção ou próximos passos")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confiança geral do diagnóstico (0.0 a 1.0)"
    )

    @field_validator("hypotheses")
    @classmethod
    def validate_hypotheses(cls, v: list[Hypothesis]) -> list[Hypothesis]:
        """Garante que todas as hipóteses têm action não vazio."""
        for h in v:
            if not h.action.strip():
                raise ValueError("Cada hipótese deve ter uma action não vazia")
        return v


# ============================================================================
# Schemas de API (Request / Response)
# ============================================================================

_ALLOWED_EXTENSIONS = (".log", ".txt")
_MAX_FILE_CHARS = 50 * 1024 * 1024  # 50 MB em caracteres


class LogFileUpload(BaseModel):
    """Schema de validação para upload de arquivo de log.

    Usado internamente após leitura do UploadFile do FastAPI.
    """

    filename: str = Field(..., min_length=1, description="Nome do arquivo enviado")
    content: str = Field(..., min_length=1, description="Conteúdo do arquivo lido")
    content_type: str = Field(default="text/plain", description="MIME type do arquivo")

    @field_validator("filename")
    @classmethod
    def validate_extension(cls, v: str) -> str:
        """Aceita apenas arquivos .log e .txt."""
        if not v.lower().endswith(_ALLOWED_EXTENSIONS):
            raise ValueError(f"Apenas arquivos {_ALLOWED_EXTENSIONS} são aceitos. Recebido: '{v}'")
        return v

    @field_validator("content")
    @classmethod
    def validate_size(cls, v: str) -> str:
        """Limita o conteúdo a 50MB (aprox. 50 * 1024 * 1024 chars)."""
        if len(v) > _MAX_FILE_CHARS:
            raise ValueError(f"Arquivo excede o limite de 50MB ({_MAX_FILE_CHARS} caracteres)")
        return v


class LogTextUpload(BaseModel):
    """Schema de request para envio de log via texto."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="Conteúdo do log em texto puro (máx. 100.000 caracteres)",
    )


class LogAnalysisResponse(BaseModel):
    """Schema de response para análise de log processado."""

    id: str = Field(..., description="UUID do registro persistido")
    analysis: AnalysisResult = Field(..., description="Resultado da análise de anomalias")
    diagnosis: AIDiagnosis = Field(..., description="Diagnóstico gerado pela IA")
    created_at: datetime = Field(..., description="Timestamp de criação do registro")
    total_entries: int = Field(default=0, ge=0, description="Total de entradas analisadas")
    summary: str = Field(default="", description="Resumo do diagnóstico para listagem")


class LogListParams(BaseModel):
    """Parâmetros de paginação para listagem de logs."""

    page: int = Field(default=1, ge=1, description="Número da página (começa em 1)")
    page_size: int = Field(default=20, ge=1, le=100, description="Itens por página (máx. 100)")


class LogListResponse(BaseModel):
    """Schema de response para listagem paginada de logs."""

    items: list[LogAnalysisResponse] = Field(..., description="Lista de logs da página atual")
    total: int = Field(..., ge=0, description="Total de registros")
    page: int = Field(..., ge=1, description="Página atual")
    page_size: int = Field(..., ge=1, description="Itens por página")
    pages: int = Field(..., ge=0, description="Total de páginas")
