"""Schemas Pydantic para modelos de dados do LogPulse IA.

Define todos os modelos que representam logs, análises e diagnósticos,
além dos schemas de request/response da API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
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

_VALID_PROBABILITIES = {"alta", "média", "media", "baixa"}


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
        """Aceita 'alta', 'média', 'media' ou 'baixa'."""
        normalized = v.strip().lower()
        if normalized not in _VALID_PROBABILITIES:
            raise ValueError(f"probability deve ser 'alta', 'média' ou 'baixa'. Recebido: '{v}'")
        # Normaliza "media" para "média"
        return "média" if normalized == "media" else normalized

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


class ErrorDetail(BaseModel):
    """Detalhes de um erro individual."""
    
    timestamp: str = Field(..., description="Timestamp do erro")
    severity: str = Field(..., description="ERROR ou CRITICAL")
    message: str = Field(..., description="Mensagem de erro")
    count: int = Field(default=1, description="Número de ocorrências")


class Issue(BaseModel):
    """Issue agrupado por padrão (similar ao Datadog/Sentry)."""
    
    model_config = {"exclude_none": True}  # Remove campos null do JSON
    
    title: str = Field(..., description="Título do problema")
    severity: str = Field(..., description="high, medium, low")
    occurrences: int = Field(..., description="Número de ocorrências")
    first_seen: str = Field(..., description="Primeira ocorrência")
    last_seen: str = Field(..., description="Última ocorrência")
    recommendation: str = Field(..., description="Recomendação de correção")
    affected_class: str | None = Field(None, description="Classe que precisa ser ajustada (extraída do stack trace)")


class LogAnalysisResponse(BaseModel):
    """Schema profissional inspirado em Datadog/Sentry."""

    model_config = {"exclude_none": True}  # Remove campos null do JSON

    # Identificação
    id: str = Field(..., description="UUID da análise")
    analyzed_at: datetime = Field(..., description="Data da análise")
    
    # Métricas agregadas (estilo Datadog)
    metrics: dict[str, int] = Field(
        ...,
        description="Métricas agregadas",
        examples=[{
            "total_logs": 128,
            "errors": 17,
            "criticals": 6
        }]
    )
    
    # Issues agrupados por padrão (estilo Sentry)
    issues: list[Issue] = Field(
        default_factory=list,
        description="Problemas detectados agrupados por padrão (cada um com seu stack trace)"
    )
    
    # Ações recomendadas (estilo Datadog Watchdog)
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Ações recomendadas em ordem de prioridade"
    )
    
    # Confiança do diagnóstico
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança (0-1)")
    
    @classmethod
    def from_full_analysis(
        cls,
        log_id: str,
        analysis: AnalysisResult,
        diagnosis: AIDiagnosis,
        created_at: datetime,
        entries: list[LogEntry] | None = None
    ) -> "LogAnalysisResponse":
        """Cria resposta no estilo Datadog/Sentry."""
        
        # Métricas agregadas (apenas erros críticos)
        metrics = {
            "total_logs": analysis.total_entries,
            "errors": analysis.severity_distribution.get(SeverityLevel.ERROR, 0),
            "criticals": analysis.severity_distribution.get(SeverityLevel.CRITICAL, 0)
        }
        
        # Agrupa erros por padrão (similar ao Sentry)
        issues = cls._group_errors_into_issues(entries, analysis)
        
        # Ações recomendadas (passa issues para priorizar HIGH severity)
        recommended_actions = cls._extract_actions(diagnosis, analysis, issues)
        
        # Usa confidence do Ollama diretamente
        confidence = diagnosis.confidence
        
        return cls(
            id=log_id,
            analyzed_at=created_at,
            metrics=metrics,
            issues=issues,
            recommended_actions=recommended_actions,
            confidence=confidence
        )
    
    @staticmethod
    def _group_errors_into_issues(
        entries: list[LogEntry] | None,
        analysis: AnalysisResult
    ) -> list[Issue]:
        """Agrupa erros similares em issues (estilo Sentry)."""
        if not entries:
            return []
        
        # Agrupa por padrão de erro (usando template_id do Drain3)
        error_patterns: dict[str, list[LogEntry]] = {}
        
        for entry in entries:
            if entry.severity.value not in ['ERROR', 'CRITICAL']:
                continue
            
            # Usa template_id se disponível, senão usa padrão da mensagem
            pattern_key = entry.template_id if entry.template_id else entry.message[:80].strip()
            
            if pattern_key not in error_patterns:
                error_patterns[pattern_key] = []
            error_patterns[pattern_key].append(entry)
        
        # Cria issues
        issues = []
        for pattern_key, error_list in error_patterns.items():
            # Determina severidade
            has_critical = any(e.severity.value == 'CRITICAL' for e in error_list)
            severity = "high" if has_critical else "medium"
            
            # Timestamps
            timestamps = [e.timestamp for e in error_list if e.timestamp]
            first_seen = min(timestamps).isoformat() if timestamps else "unknown"
            last_seen = max(timestamps).isoformat() if timestamps else "unknown"
            
            # Título do issue (usa a primeira mensagem como representante)
            title = error_list[0].message[:100].strip()
            
            # Recomendação baseada no padrão
            recommendation = LogAnalysisResponse._get_recommendation_for_pattern(title)
            
            # Extrai classe afetada do stack trace (se disponível)
            # Passa os stack_traces completos do AnalysisResult para busca mais precisa
            affected_class = LogAnalysisResponse._extract_affected_class(
                error_list, stack_traces=analysis.stack_traces
            )
            
            issues.append(Issue(
                title=title,
                severity=severity,
                occurrences=len(error_list),
                first_seen=first_seen,
                last_seen=last_seen,
                recommendation=recommendation,
                affected_class=affected_class
            ))
        
        # Ordena por severidade e ocorrências
        issues.sort(key=lambda x: (
            0 if x.severity == "high" else 1,
            -x.occurrences
        ))
        
        return issues[:10]  # Top 10 issues
    
    @staticmethod
    def _extract_affected_class(error_list: list, stack_traces: list[str] | None = None) -> str | None:
        """Extrai a classe afetada do stack trace (primeira classe do projeto encontrada).

        Busca primeiro nos stack traces completos do AnalysisResult (mais confiável),
        depois no raw_content de cada entry como fallback.

        Args:
            error_list: Lista de LogEntry com erros similares.
            stack_traces: Stack traces completos extraídos pelo detector (opcional).

        Returns:
            Nome da classe afetada no formato 'ClassName.method_name' ou None.
        """
        import re

        # Padrão para arquivos Python do projeto (não de bibliotecas do sistema)
        # Exemplo: File "/app/services/payment_service.py", line 89, in process_payment
        pattern = r'File "(/app/[^"]+\.py)", line \d+(?:, in (\w+))?'

        def _extract_from_text(text: str) -> str | None:
            matches = re.findall(pattern, text)
            if matches:
                file_path, method_name = matches[0]
                file_name = file_path.split('/')[-1].replace('.py', '')
                class_name = ''.join(word.capitalize() for word in file_name.split('_'))
                return f"{class_name}.{method_name}" if method_name else class_name
            return None

        # 1. Busca nos stack traces completos (mais confiável — contém o traceback inteiro)
        if stack_traces:
            for trace in stack_traces:
                result = _extract_from_text(trace)
                if result:
                    return result

        # 2. Fallback: busca no raw_content de cada entry
        for entry in error_list:
            raw = getattr(entry, 'raw_content', '') or ''
            result = _extract_from_text(raw)
            if result:
                return result

        return None
    
    @staticmethod
    def _get_recommendation_for_pattern(pattern: str) -> str:
        """Retorna recomendação baseada no padrão de erro."""
        pattern_lower = pattern.lower()

        if "pool" in pattern_lower and ("connection" in pattern_lower or "exhaust" in pattern_lower):
            return "Aumentar pool de conexões do banco de dados e revisar connection leaks"
        elif "circuit breaker" in pattern_lower:
            return "Aguardar circuit breaker fechar ou forçar reset manual; investigar causa raiz do serviço dependente"
        elif "pool" in pattern_lower or "connection" in pattern_lower:
            return "Aumentar pool de conexões do banco de dados"
        elif "memory" in pattern_lower or "oom" in pattern_lower:
            return "Otimizar uso de memória ou aumentar recursos do servidor"
        elif "timeout" in pattern_lower:
            return "Aumentar timeout ou otimizar query/operação lenta"
        elif "payment" in pattern_lower or "stripe" in pattern_lower or "charge" in pattern_lower:
            return "Verificar disponibilidade do gateway de pagamento e configurar retry com backoff"
        elif "retry" in pattern_lower or "max retries" in pattern_lower:
            return "Revisar política de retry e implementar circuit breaker para o serviço externo"
        elif "503" in pattern_lower or "service unavailable" in pattern_lower:
            return "Verificar saúde do serviço dependente e configurar fallback"
        elif "500" in pattern_lower or "internal server" in pattern_lower:
            return "Verificar logs do servidor para causa específica do erro interno"
        elif "validation" in pattern_lower or "422" in pattern_lower or "unprocessable" in pattern_lower:
            return "Revisar validação de entrada e retornar mensagens de erro claras ao cliente"
        elif "account locked" in pattern_lower or "too many" in pattern_lower or "429" in pattern_lower:
            return "Revisar política de rate limiting e notificar usuário sobre bloqueio"
        elif "redis" in pattern_lower or "cache" in pattern_lower:
            return "Verificar conectividade com Redis e implementar fallback para banco de dados"
        elif "email" in pattern_lower or "smtp" in pattern_lower or "notification" in pattern_lower:
            return "Verificar configuração do servidor SMTP e implementar fila de retry para emails"
        elif "disk" in pattern_lower or "log rotation" in pattern_lower:
            return "Configurar rotação automática de logs e monitorar espaço em disco"
        elif "spike" in pattern_lower:
            return "Investigar causa do pico de erros e configurar alertas automáticos"
        elif "fetch" in pattern_lower or "failed to" in pattern_lower:
            return "Verificar disponibilidade do recurso e adicionar tratamento de erro adequado"
        else:
            return "Analisar stack trace para identificar causa raiz"
    
    @staticmethod
    def _extract_actions(diagnosis: AIDiagnosis, analysis: AnalysisResult, issues: list[Issue]) -> list[str]:
        """Extrai ações recomendadas em ordem de prioridade.
        
        PRIORIDADE:
        1. Recomendações de issues HIGH severity
        2. Ação principal do diagnóstico IA
        3. Ações das hipóteses IA (ordenadas por probabilidade)
        4. Ações adicionais baseadas na análise
        """
        actions = []
        seen_actions = set()  # Evita duplicatas
        
        # 1. PRIORIDADE MÁXIMA: Recomendações de issues HIGH
        high_issues = [i for i in issues if i.severity == "high"]
        for issue in high_issues:
            if issue.recommendation and issue.recommendation not in seen_actions:
                actions.append(issue.recommendation)
                seen_actions.add(issue.recommendation)
        
        # 2. Ação principal do diagnóstico IA
        if diagnosis.suggested_fix and diagnosis.suggested_fix not in seen_actions:
            actions.append(diagnosis.suggested_fix)
            seen_actions.add(diagnosis.suggested_fix)
        
        # 3. Ações das hipóteses (ordenadas por probabilidade: alta > média > baixa)
        sorted_hypotheses = sorted(
            diagnosis.hypotheses,
            key=lambda h: {"alta": 0, "média": 1, "baixa": 2}.get(h.probability, 3)
        )
        
        for hypothesis in sorted_hypotheses:
            if hypothesis.action and hypothesis.action not in seen_actions:
                actions.append(hypothesis.action)
                seen_actions.add(hypothesis.action)
        
        # 4. Ações adicionais baseadas na análise
        if len(analysis.spikes) > 0:
            spike_action = "Configurar alertas para detecção de spikes futuros"
            if spike_action not in seen_actions:
                actions.append(spike_action)
                seen_actions.add(spike_action)
        
        if len(analysis.stack_traces) > 0:
            trace_action = f"Analise os {len(analysis.stack_traces)} stack traces detectados e os templates de erro mais frequentes"
            if trace_action not in seen_actions:
                actions.append(trace_action)
                seen_actions.add(trace_action)
        
        # 5. Ações de issues MEDIUM severity (se ainda houver espaço)
        medium_issues = [i for i in issues if i.severity == "medium"]
        for issue in medium_issues:
            if issue.recommendation and issue.recommendation not in seen_actions:
                actions.append(issue.recommendation)
                seen_actions.add(issue.recommendation)
        
        # Retorna todas as ações únicas (removido o limite de 5)
        return actions


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
