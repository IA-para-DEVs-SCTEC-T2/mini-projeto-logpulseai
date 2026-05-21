"""Hierarquia de exceções customizadas do LogPulse IA.

Todas as exceções do sistema herdam de LogPulseError,
permitindo captura genérica quando necessário.
"""


class LogPulseError(Exception):
    """Exceção base do LogPulse IA."""


class ConfigError(LogPulseError):
    """Erro de configuração (logpulse.toml inválido ou ausente)."""


class SourceError(LogPulseError):
    """Erro ao ler fonte de log (arquivo não encontrado, permissão negada)."""


class ParserError(LogPulseError):
    """Erro ao parsear linha de log individual."""


class ParsingError(LogPulseError):
    """Erro ao processar conteúdo de log (nenhuma entrada válida, formato inválido)."""


class ValidationError(LogPulseError):
    """Erro de validação de dados de entrada."""


class NotFoundError(LogPulseError):
    """Recurso não encontrado."""


class StorageError(LogPulseError):
    """Erro ao acessar o banco de dados (leitura, escrita, conexão)."""


class AnalysisError(LogPulseError):
    """Erro durante a análise do log stream."""


class AnalyzerError(LogPulseError):
    """Erro no componente analyzer.

    .. deprecated::
        Use :class:`AnalysisError` em código novo.
        Mantido apenas para compatibilidade com testes legados.
    """


class AIEngineError(LogPulseError):
    """Erro genérico ao comunicar com LLM."""


class AIEngineTimeoutError(AIEngineError):
    """LLM não respondeu dentro do tempo limite."""


class AIEngineUnavailableError(AIEngineError):
    """Serviço de LLM indisponível (Ollama não está rodando)."""
