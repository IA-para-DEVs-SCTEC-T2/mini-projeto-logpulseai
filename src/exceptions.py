"""Hierarquia de exceções customizadas do LogPulse IA."""


class LogPulseError(Exception):
    """Exceção base do LogPulse IA."""


class ConfigError(LogPulseError):
    """Erro de configuração (logpulse.toml inválido ou ausente)."""


class SourceError(LogPulseError):
    """Erro ao ler fonte de log (arquivo não encontrado, permissão negada)."""


class ParserError(LogPulseError):
    """Erro ao parsear linha de log."""


class ParsingError(ParserError):
    """Erro ao parsear linha de log (alias para ParserError)."""


class AIEngineError(LogPulseError):
    """Erro ao comunicar com LLM (API key inválida, timeout, serviço indisponível)."""


class AIEngineUnavailableError(AIEngineError):
    """Erro quando o serviço de IA (Ollama) não está disponível."""


class AIEngineTimeoutError(AIEngineError):
    """Erro quando a chamada ao serviço de IA excede o timeout."""


class AnalyzerError(LogPulseError):
    """Erro durante a análise do log stream."""


class StorageError(LogPulseError):
    """Erro ao persistir ou recuperar dados do repositório."""


class ValidationError(LogPulseError):
    """Erro de validação de dados de entrada."""


class NotFoundError(LogPulseError):
    """Erro quando um recurso não é encontrado."""


class ParsingError(LogPulseError):
    """Erro ao fazer parsing de dados."""


class AnalysisError(LogPulseError):
    """Erro durante a análise de logs."""
