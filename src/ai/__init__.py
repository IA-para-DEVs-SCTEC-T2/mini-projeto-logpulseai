"""Módulo de integração com motores de IA do LogPulse IA.

Exporta a interface abstrata AIEngine e a implementação OllamaAIEngine.
"""

from src.ai.base import AIEngine
from src.ai.ollama_engine import OllamaAIEngine

__all__ = ["AIEngine", "OllamaAIEngine"]
