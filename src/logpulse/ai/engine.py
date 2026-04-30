"""Integração com LLMs para diagnóstico e hipóteses de causa raiz."""

from __future__ import annotations

import os

from logpulse.models import AnalysisResult


class AIEngine:
    """Envia resultados de análise para um LLM e retorna diagnóstico."""

    def __init__(self, model: str = "gpt-4o", endpoint: str | None = None) -> None:
        self._model = model
        self._endpoint = endpoint
        self._api_key = os.environ.get("LOGPULSE_API_KEY") or os.environ.get("OPENAI_API_KEY")

    def diagnose(self, result: AnalysisResult, sample_lines: list[str]) -> str:
        """
        Envia o resumo da análise para o LLM e retorna hipóteses de causa raiz.

        Requer LOGPULSE_API_KEY ou OPENAI_API_KEY no ambiente.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
        except ImportError:
            return "⚠️  Dependências de IA não instaladas. Execute: pip install langchain-openai"

        if not self._api_key and not self._endpoint:
            return "⚠️  Configure LOGPULSE_API_KEY ou um endpoint Ollama em logpulse.toml."

        prompt = self._build_prompt(result, sample_lines)

        kwargs: dict[str, object] = {"model": self._model}
        if self._endpoint:
            kwargs["base_url"] = self._endpoint
            kwargs["api_key"] = "ollama"
        else:
            kwargs["api_key"] = self._api_key  # type: ignore[assignment]

        llm = ChatOpenAI(**kwargs)  # type: ignore[arg-type]
        response = llm.invoke([HumanMessage(content=prompt)])
        return str(response.content)

    def _build_prompt(self, result: AnalysisResult, sample_lines: list[str]) -> str:
        """Constrói o prompt enviado ao LLM."""
        samples = "\n".join(sample_lines[:20])
        anomalies = "\n".join(result.anomalies) or "Nenhuma"
        spikes = "\n".join(result.spikes) or "Nenhum"

        return (
            f"Você é um especialista em SRE analisando logs de produção.\n\n"
            f"Resumo da análise:\n"
            f"- Total de entradas: {result.total_entries}\n"
            f"- Erros: {result.error_count}\n"
            f"- Avisos: {result.warning_count}\n\n"
            f"Anomalias detectadas:\n{anomalies}\n\n"
            f"Spikes de erros:\n{spikes}\n\n"
            f"Amostra de linhas de log:\n{samples}\n\n"
            f"Com base nessas informações, forneça:\n"
            f"1. Hipóteses de causa raiz\n"
            f"2. Sugestões de ação imediata\n"
            f"3. Recomendações de longo prazo"
        )
