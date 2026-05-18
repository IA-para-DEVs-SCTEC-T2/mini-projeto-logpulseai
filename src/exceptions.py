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


class AIEngineTimeoutError(AIEngineError):
    """Erro de timeout ao comunicar com o LLM."""


class AIEngineUnavailableError(AIEngineError):
    """Erro quando o serviço de LLM está indisponível."""


class AnalyzerError(LogPulseError):
    """Erro durante a análise do log stream."""


class AnalysisError(LogPulseError):
    """Erro durante a análise do log stream (alias para AnalyzerError)."""


class StorageError(LogPulseError):
    """Erro de persistência (falha ao salvar/recuperar dados do SQLite)."""


class NotFoundError(LogPulseError):
    """Erro quando um recurso não é encontrado."""


class ValidationError(LogPulseError):
    """Erro de validação de dados."""
