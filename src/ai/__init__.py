"""Módulo de integração com motores de IA do LogPulse IA.

Exporta a interface abstrata AIEngine e a implementação OllamaAIEngine.
"""

from src.ai.base import AIEngine
from src.ai.health_check import check_ollama_available, check_ollama_http, check_ollama_tcp
from src.ai.ollama_engine import OllamaAIEngine

__all__ = [
    "AIEngine",
    "OllamaAIEngine",
    "check_ollama_available",
    "check_ollama_http",
    "check_ollama_tcp",
]
