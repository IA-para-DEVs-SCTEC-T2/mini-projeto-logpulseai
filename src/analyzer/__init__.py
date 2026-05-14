"""Módulo de análise de anomalias em logs do LogPulse IA.

Fornece interfaces abstratas e implementações concretas para
detecção de anomalias, spikes e padrões em streams de log.
"""

from src.analyzer.base import LogAnalyzer

__all__ = ["LogAnalyzer"]
