"""Hierarquia de exceções customizadas do LogPulse IA."""


class LogPulseError(Exception):
    """Exceção base do LogPulse IA."""


class ConfigError(LogPulseError):
    """Erro de configuração (logpulse.toml inválido ou ausente)."""


class SourceError(LogPulseError):
    """Erro ao ler fonte de log (arquivo não encontrado, permissão negada)."""


class ParserError(LogPulseError):
    """Erro ao parsear linha de log."""


class AIEngineError(LogPulseError):
    """Erro ao comunicar com LLM (API key inválida, timeout, serviço indisponível)."""


class AnalyzerError(LogPulseError):
    """Erro durante a análise do log stream."""
