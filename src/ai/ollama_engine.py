"""Implementação do AIEngine usando Ollama/LLaMA 3 via OpenAI SDK."""

from __future__ import annotations

import json
import random
import time

import openai

from src.ai.base import AIEngine
from src.ai.health_check import check_ollama_tcp
from src.core.config import get_settings
from src.core.logging import get_logger
from src.exceptions import AIEngineTimeoutError
from src.models.schemas import AIDiagnosis, AnalysisResult, LogEntry, SeverityLevel

# ---------------------------------------------------------------------------
# Constantes de configuração
# ---------------------------------------------------------------------------

_OLLAMA_BASE_URL = "http://localhost:11434/v1"
_OLLAMA_HOST = "localhost"
_OLLAMA_PORT = 11434
_MODEL_NAME = "llama3.2:3b"

# Timeout por chamada ao Ollama (segundos) — alinhado com RF-05.7 e RNF-08
_CALL_TIMEOUT_SECONDS = 120

# Configuração de retry com backoff exponencial
_MAX_RETRIES = 2  # 2 tentativas
_RETRY_DELAYS = [1, 2]  # segundos entre tentativas

# Amostragem estratificada
_MAX_SAMPLE_ENTRIES = 10  # Reduzido para processar mais rápido
_ERROR_RATIO = 0.80   # 80% de erros (ERROR + CRITICAL) - foco em problemas
_WARNING_RATIO = 0.15  # 15% de warnings
_OTHER_RATIO = 0.05   # 5% de outros (INFO, DEBUG)

# Níveis considerados "erro" para amostragem
_ERROR_LEVELS = {SeverityLevel.ERROR, SeverityLevel.CRITICAL}
_WARNING_LEVELS = {SeverityLevel.WARNING}

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Prompt do sistema
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Você é um especialista em análise de logs. Responda APENAS com JSON válido.

REGRAS:
1. JSON válido, sem markdown
2. "probability": "alta", "média" ou "baixa"
3. Máximo 2 hipóteses
4. Seja direto e técnico
5. "confidence": valor OBRIGATORIAMENTE calculado assim (some os pontos):
   - Base: 0.5
   - Stack traces presentes nos logs: +0.2
   - Múltiplas ocorrências do mesmo erro (>=5): +0.15
   - Spike de erros detectado: +0.15
   - Padrão claro identificado (causa óbvia): +0.1
   - Informação insuficiente ou logs muito genéricos: -0.2
   - Mínimo: 0.4, Máximo: 0.95

Schema:
{
  "summary": "Resumo do problema",
  "probable_cause": "Causa raiz específica",
  "hypotheses": [
    {
      "description": "Hipótese 1",
      "probability": "alta",
      "action": "Ação concreta",
      "related_line": null
    }
  ],
  "suggested_fix": "Solução principal",
  "confidence": 0.85
}"""


def _build_user_prompt(analysis: AnalysisResult, sample_entries: list[LogEntry]) -> str:
    """Constrói prompt simplificado focado no problema.
    
    OTIMIZAÇÃO: Recebe apenas entradas ERROR/CRITICAL para reduzir payload.
    Inclui contexto para o LLM calcular confidence adequadamente.
    """
    lines = [
        f"Total: {analysis.total_entries} | Erros: {analysis.error_count}",
    ]

    # Contexto para confidence
    confidence_factors = []
    
    # Spike
    if analysis.spikes:
        spike = analysis.spikes[0]
        lines.append(f"SPIKE: {spike.error_count} erros em {int((spike.end_time - spike.start_time).total_seconds())}s")
        confidence_factors.append("spike detectado")

    # Stack trace principal (apenas primeiras 3 linhas)
    if analysis.stack_traces:
        lines.append("Stack trace:")
        for line in analysis.stack_traces[0].split("\n")[:3]:
            lines.append(f"  {line.strip()}")
        confidence_factors.append(f"{len(analysis.stack_traces)} stack traces")

    # Top 3 erros (já filtrados, todos são ERROR/CRITICAL)
    if sample_entries:
        lines.append("Erros:")
        for e in sample_entries[:3]:
            lines.append(f"  {e.raw_content[:80]}")
        
        # Verifica se há padrão (múltiplas ocorrências)
        if len(sample_entries) >= 5:
            confidence_factors.append("múltiplas ocorrências")
    
    # Adiciona dica de confidence ao final
    if confidence_factors:
        lines.append(f"\nEvidências: {', '.join(confidence_factors)}")
    else:
        lines.append("\nEvidências: informação limitada")

    return "\n".join(lines)


def _filter_errors_only(entries: list[LogEntry], max_entries: int = _MAX_SAMPLE_ENTRIES) -> list[LogEntry]:
    """Filtra apenas entradas ERROR/CRITICAL para otimizar performance.
    
    OTIMIZAÇÃO: Envia apenas erros críticos ao LLM, reduzindo drasticamente
    o tamanho do payload e tempo de resposta.
    
    Args:
        entries: Lista completa de entradas de log.
        max_entries: Número máximo de entradas na amostra (padrão: 10).

    Returns:
        Lista com no máximo max_entries erros (ERROR/CRITICAL).
    """
    if not entries:
        return []

    # Filtra apenas ERROR e CRITICAL
    errors = [e for e in entries if e.severity in _ERROR_LEVELS]
    
    if not errors:
        logger.warning("no_errors_found", total_entries=len(entries))
        return []
    
    # Se há poucos erros, retorna todos
    if len(errors) <= max_entries:
        return errors
    
    # Amostra aleatória dos erros
    return random.sample(errors, max_entries)


def _check_ollama_availability() -> None:
    """Verifica se o Ollama está disponível na porta 11434.

    Delega ao módulo health_check para verificação TCP.
    Lança AIEngineUnavailableError se a conexão falhar.

    Raises:
        AIEngineUnavailableError: Se o Ollama não estiver acessível.
    """
    check_ollama_tcp(host=_OLLAMA_HOST, port=_OLLAMA_PORT)


def _parse_llm_response(content: str) -> AIDiagnosis:
    """Parseia a resposta do LLM para um objeto AIDiagnosis.

    Args:
        content: Conteúdo textual retornado pelo LLM.

    Returns:
        Objeto AIDiagnosis validado pelo Pydantic.

    Raises:
        pydantic.ValidationError: Se a resposta não atender ao schema.
        json.JSONDecodeError: Se o conteúdo não for JSON válido.
    """
    # Remove possíveis blocos de código markdown
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove primeira linha (```json ou ```) e última linha (```)
        cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    data = json.loads(cleaned)
    return AIDiagnosis.model_validate(data)


def _adjust_confidence(diagnosis: AIDiagnosis, analysis: AnalysisResult) -> AIDiagnosis:
    """Ajusta a confidence do LLM baseado nos dados reais quando subestimada.

    O LLM às vezes retorna confidence conservadora (ex: 0.4) mesmo com
    evidências claras. Esta função aplica um piso mínimo baseado nos dados.

    Args:
        diagnosis: Diagnóstico retornado pelo LLM.
        analysis: Resultado da análise com dados concretos.

    Returns:
        Diagnóstico com confidence ajustada se necessário.
    """
    # Calcula confidence mínima baseada nas evidências concretas
    min_confidence = 0.5  # base

    if analysis.stack_traces:
        min_confidence += 0.15  # stack traces = evidência forte

    critical_count = analysis.severity_distribution.get(SeverityLevel.CRITICAL, 0)
    if critical_count > 0:
        min_confidence += 0.1  # erros críticos = problema claro

    if analysis.spikes:
        min_confidence += 0.1  # spike = padrão temporal identificado

    if analysis.error_count >= 5:
        min_confidence += 0.05  # múltiplas ocorrências

    min_confidence = min(min_confidence, 0.95)

    if diagnosis.confidence < min_confidence:
        logger.info(
            "confidence_adjusted",
            original=diagnosis.confidence,
            adjusted=round(min_confidence, 2),
            reason="LLM subestimou baseado nas evidências disponíveis"
        )
        # Pydantic v2: cria nova instância com confidence ajustada
        return diagnosis.model_copy(update={"confidence": round(min_confidence, 2)})

    return diagnosis


class OllamaAIEngine(AIEngine):
    """Motor de IA usando Ollama/LLaMA 3 via OpenAI SDK.

    Implementa o contrato AIEngine utilizando o servidor Ollama local
    como backend de LLM, com suporte a timeout, retry com backoff
    exponencial e validação de resposta via Pydantic.

    Attributes:
        _client: Cliente OpenAI SDK configurado para o Ollama local.
        _model: Nome do modelo LLM a ser utilizado.

    Example:
        >>> engine = OllamaAIEngine()
        >>> diagnosis = engine.diagnose(analysis_result, sample_entries)
        >>> print(diagnosis.summary)
    """

    def __init__(
        self,
        base_url: str = _OLLAMA_BASE_URL,
        model: str = _MODEL_NAME,
        timeout: int = _CALL_TIMEOUT_SECONDS,
    ) -> None:
        """Inicializa o OllamaAIEngine com cliente OpenAI SDK.

        Os valores padrão são lidos das configurações da aplicação (Settings),
        garantindo que variáveis de ambiente como LOGPULSE_OLLAMA_MODEL e
        LOGPULSE_OLLAMA_TIMEOUT sejam respeitadas.

        Args:
            base_url: URL base do servidor Ollama.
            model: Nome do modelo LLM (padrão: llama3.2:3b via settings).
            timeout: Timeout por chamada em segundos (padrão: 120s via settings).
        """
        self._model = model
        self._client = openai.OpenAI(
            base_url=base_url,
            api_key="ollama",  # Ollama não requer API key real
            timeout=timeout,
            max_retries=0,  # Desabilita retry do OpenAI SDK — gerenciado internamente
        )

    def diagnose(
        self,
        analysis: AnalysisResult,
        sample_entries: list[LogEntry],
    ) -> AIDiagnosis:
        """Gera diagnóstico inteligente a partir da análise de logs.

        Verifica disponibilidade do Ollama, realiza amostragem estratificada,
        envia prompt ao LLaMA 3 e valida a resposta com Pydantic.

        Args:
            analysis: Resultado da análise de anomalias.
            sample_entries: Lista de entradas de log para amostragem.

        Returns:
            Diagnóstico estruturado com hipóteses e sugestões.

        Raises:
            AIEngineUnavailableError: Se o Ollama não estiver disponível.
            AIEngineTimeoutError: Se todas as tentativas esgotarem o timeout.
        """
        logger.info(
            "diagnosis_started",
            model=self._model,
            total_entries=len(sample_entries),
            error_count=analysis.error_count,
            warning_count=analysis.warning_count
        )
        
        # Verifica disponibilidade antes de processar
        _check_ollama_availability()

        # OTIMIZAÇÃO: Filtra apenas ERROR/CRITICAL para reduzir payload
        errors_only = _filter_errors_only(sample_entries)
        
        logger.info(
            "errors_filtered",
            original_count=len(sample_entries),
            errors_count=len(errors_only),
            performance_gain=f"{(1 - len(errors_only)/max(len(sample_entries), 1)) * 100:.1f}% reduction"
        )

        # Constrói prompts (apenas com erros críticos)
        user_prompt = _build_user_prompt(analysis, errors_only)

        # Tenta com retry e backoff exponencial
        last_exception: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            logger.info(
                "ollama_request_attempt",
                attempt=attempt,
                max_retries=_MAX_RETRIES,
                model=self._model
            )
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,  # Muito baixo para respostas mais determinísticas
                    max_tokens=300,   # Reduzido para forçar respostas mais curtas
                )

                content = response.choices[0].message.content or ""
                diagnosis = _parse_llm_response(content)

                # Ajusta confidence se o LLM subestimou baseado nos dados reais
                diagnosis = _adjust_confidence(diagnosis, analysis)

                logger.info(
                    "diagnosis_completed",
                    model=self._model,
                    attempt=attempt,
                    hypotheses_count=len(diagnosis.hypotheses),
                    confidence=diagnosis.confidence
                )
                
                return diagnosis

            except (openai.APITimeoutError, openai.APIConnectionError) as exc:
                last_exception = exc
                logger.warning(
                    "ollama_request_failed",
                    attempt=attempt,
                    max_retries=_MAX_RETRIES,
                    error_type=type(exc).__name__,
                    error=str(exc),
                    will_retry=attempt < _MAX_RETRIES
                )
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS[attempt - 1]
                    logger.debug("retry_backoff", delay_seconds=delay)
                    time.sleep(delay)

        logger.error(
            "diagnosis_failed",
            model=self._model,
            max_retries=_MAX_RETRIES,
            last_error=str(last_exception)
        )
        
        raise AIEngineTimeoutError(
            f"Ollama não respondeu após {_MAX_RETRIES} tentativas. "
            f"Último erro: {last_exception}"
        ) from last_exception
