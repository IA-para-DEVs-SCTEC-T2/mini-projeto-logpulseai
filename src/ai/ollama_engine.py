"""Implementação do AIEngine usando Ollama/LLaMA 3 via OpenAI SDK."""

from __future__ import annotations

import json
import logging
import math
import random
import socket
import time
from typing import List

import openai

from src.ai.base import AIEngine
from src.exceptions import AIEngineTimeoutError, AIEngineUnavailableError
from src.models.schemas import AIDiagnosis, AnalysisResult, Hypothesis, LogEntry, SeverityLevel

# ---------------------------------------------------------------------------
# Constantes de configuração
# ---------------------------------------------------------------------------

_OLLAMA_BASE_URL = "http://localhost:11434/v1"
_OLLAMA_HOST = "localhost"
_OLLAMA_PORT = 11434
_MODEL_NAME = "llama3"

# Timeout por chamada ao Ollama (segundos)
_CALL_TIMEOUT_SECONDS = 30

# Configuração de retry com backoff exponencial
_MAX_RETRIES = 3
_RETRY_DELAYS = [1, 2, 4]  # segundos entre tentativas

# Amostragem estratificada
_MAX_SAMPLE_ENTRIES = 50
_ERROR_RATIO = 0.70   # 70% de erros (ERROR + CRITICAL)
_WARNING_RATIO = 0.20  # 20% de warnings
_OTHER_RATIO = 0.10   # 10% de outros (INFO, DEBUG)

# Níveis considerados "erro" para amostragem
_ERROR_LEVELS = {SeverityLevel.ERROR, SeverityLevel.CRITICAL}
_WARNING_LEVELS = {SeverityLevel.WARNING}

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt do sistema
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Você é um especialista em análise de logs de sistemas de produção.
Sua tarefa é analisar logs fornecidos e gerar um diagnóstico estruturado em JSON.

Regras obrigatórias:
1. Responda APENAS com JSON válido, sem texto adicional antes ou depois.
2. O JSON deve seguir exatamente o schema fornecido.
3. Gere EXATAMENTE 3 ou mais hipóteses de causa raiz.
4. Cada hipótese DEVE ter um campo "action" não vazio com uma ação concreta.
5. O campo "probability" deve ser exatamente "alta", "média" ou "baixa".
6. Baseie-se APENAS nas informações fornecidas — não invente eventos ou timestamps.
7. As hipóteses devem ser ordenadas da maior para a menor probabilidade.

Schema JSON esperado:
{
  "summary": "Resumo claro do problema identificado",
  "probable_cause": "Causa raiz mais provável",
  "hypotheses": [
    {
      "description": "Descrição da hipótese",
      "probability": "alta",
      "action": "Ação concreta para investigar ou corrigir",
      "related_line": null
    }
  ],
  "suggested_fix": "Sugestão de correção ou próximos passos",
  "confidence": 0.85
}"""


def _build_user_prompt(analysis: AnalysisResult, sample_entries: List[LogEntry]) -> str:
    """Constrói o prompt do usuário com os dados de análise e amostras.

    Args:
        analysis: Resultado da análise de anomalias.
        sample_entries: Amostra estratificada de entradas de log.

    Returns:
        Prompt formatado para envio ao LLM.
    """
    lines = [
        "## Análise de Logs",
        "",
        f"**Total de entradas:** {analysis.total_entries}",
        f"**Erros (ERROR + CRITICAL):** {analysis.error_count}",
        f"**Warnings:** {analysis.warning_count}",
        f"**Dados insuficientes:** {analysis.insufficient_data}",
        "",
    ]

    # Distribuição de severidade
    if analysis.severity_distribution:
        lines.append("**Distribuição por severidade:**")
        for level, count in analysis.severity_distribution.items():
            lines.append(f"  - {level.value}: {count}")
        lines.append("")

    # Spikes detectados
    if analysis.spikes:
        lines.append(f"**Spikes detectados:** {len(analysis.spikes)}")
        for spike in analysis.spikes:
            lines.append(
                f"  - {spike.error_count} erros entre "
                f"{spike.start_time.isoformat()} e {spike.end_time.isoformat()}"
            )
        lines.append("")

    # Stack traces
    if analysis.stack_traces:
        lines.append(f"**Stack traces detectados:** {len(analysis.stack_traces)}")
        for i, trace in enumerate(analysis.stack_traces[:3], 1):
            lines.append(f"  Stack trace {i}:")
            for trace_line in trace.split("\n")[:5]:
                lines.append(f"    {trace_line}")
        lines.append("")

    # Templates
    if analysis.templates:
        lines.append(f"**Templates de log ({len(analysis.templates)} padrões):**")
        for tmpl in analysis.templates[:5]:
            lines.append(f"  - [{tmpl.occurrences}x] {tmpl.pattern}")
        lines.append("")

    # Amostras de log
    if sample_entries:
        lines.append(f"**Amostras de log ({len(sample_entries)} entradas):**")
        for entry in sample_entries:
            ts = entry.timestamp.isoformat() if entry.timestamp else "sem timestamp"
            lines.append(f"  [{entry.severity.value}] {ts} — {entry.raw_content[:200]}")
        lines.append("")

    lines.append("Gere o diagnóstico em JSON conforme o schema especificado.")

    return "\n".join(lines)


def _stratified_sample(entries: List[LogEntry], max_entries: int = _MAX_SAMPLE_ENTRIES) -> List[LogEntry]:
    """Realiza amostragem estratificada das entradas de log.

    Seleciona entradas respeitando as proporções:
    - 70% de erros (ERROR + CRITICAL)
    - 20% de warnings (WARNING)
    - 10% de outros (INFO, DEBUG)

    Args:
        entries: Lista completa de entradas de log.
        max_entries: Número máximo de entradas na amostra (padrão: 50).

    Returns:
        Lista amostrada com no máximo max_entries entradas.
    """
    if not entries:
        return []

    if len(entries) <= max_entries:
        return list(entries)

    # Separa por categoria
    errors = [e for e in entries if e.severity in _ERROR_LEVELS]
    warnings = [e for e in entries if e.severity in _WARNING_LEVELS]
    others = [e for e in entries if e.severity not in _ERROR_LEVELS and e.severity not in _WARNING_LEVELS]

    # Calcula quantidades por categoria
    n_errors = math.floor(max_entries * _ERROR_RATIO)
    n_warnings = math.floor(max_entries * _WARNING_RATIO)
    n_others = max_entries - n_errors - n_warnings

    # Ajusta se não há entradas suficientes em alguma categoria
    actual_errors = min(n_errors, len(errors))
    actual_warnings = min(n_warnings, len(warnings))
    actual_others = min(n_others, len(others))

    # Redistribui slots não utilizados
    remaining = max_entries - actual_errors - actual_warnings - actual_others
    if remaining > 0:
        # Tenta completar com erros primeiro, depois warnings, depois outros
        extra_errors = min(remaining, len(errors) - actual_errors)
        actual_errors += extra_errors
        remaining -= extra_errors

    if remaining > 0:
        extra_warnings = min(remaining, len(warnings) - actual_warnings)
        actual_warnings += extra_warnings
        remaining -= extra_warnings

    if remaining > 0:
        extra_others = min(remaining, len(others) - actual_others)
        actual_others += extra_others

    # Amostra aleatória de cada categoria
    sampled_errors = random.sample(errors, actual_errors) if actual_errors > 0 else []
    sampled_warnings = random.sample(warnings, actual_warnings) if actual_warnings > 0 else []
    sampled_others = random.sample(others, actual_others) if actual_others > 0 else []

    return sampled_errors + sampled_warnings + sampled_others


def _check_ollama_availability() -> None:
    """Verifica se o Ollama está disponível na porta 11434.

    Tenta estabelecer uma conexão TCP com o servidor Ollama.
    Lança AIEngineUnavailableError se a conexão falhar.

    Raises:
        AIEngineUnavailableError: Se o Ollama não estiver acessível.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((_OLLAMA_HOST, _OLLAMA_PORT))
        sock.close()
        if result != 0:
            raise AIEngineUnavailableError(
                f"Ollama não está disponível em {_OLLAMA_BASE_URL}. "
                "Execute: ollama serve"
            )
    except OSError as exc:
        raise AIEngineUnavailableError(
            f"Ollama não está disponível em {_OLLAMA_BASE_URL}. "
            "Execute: ollama serve"
        ) from exc


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

        Args:
            base_url: URL base do servidor Ollama.
            model: Nome do modelo LLM (padrão: llama3).
            timeout: Timeout por chamada em segundos (padrão: 30).
        """
        self._model = model
        self._client = openai.OpenAI(
            base_url=base_url,
            api_key="ollama",  # Ollama não requer API key real
            timeout=timeout,
        )

    def diagnose(
        self,
        analysis: AnalysisResult,
        sample_entries: List[LogEntry],
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
        # Verifica disponibilidade antes de processar
        _check_ollama_availability()

        # Amostragem estratificada
        sampled = _stratified_sample(sample_entries)

        # Constrói prompts
        user_prompt = _build_user_prompt(analysis, sampled)

        # Tenta com retry e backoff exponencial
        last_exception: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            logger.info("Tentativa %d de %d ao Ollama", attempt, _MAX_RETRIES)
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                )

                content = response.choices[0].message.content or ""
                return _parse_llm_response(content)

            except (openai.APITimeoutError, openai.APIConnectionError) as exc:
                last_exception = exc
                logger.warning(
                    "Tentativa %d falhou: %s. %s",
                    attempt,
                    type(exc).__name__,
                    "Aguardando antes de tentar novamente..." if attempt < _MAX_RETRIES else "Esgotadas todas as tentativas.",
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAYS[attempt - 1])

        raise AIEngineTimeoutError(
            f"Ollama não respondeu após {_MAX_RETRIES} tentativas. "
            f"Último erro: {last_exception}"
        ) from last_exception
