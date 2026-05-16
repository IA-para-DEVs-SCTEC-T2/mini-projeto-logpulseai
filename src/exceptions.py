"""Hierarquia de exceções customizadas do LogPulse IA.

Define todas as exceções específicas do domínio, organizadas em uma
hierarquia que facilita o tratamento granular de erros.

Hierarquia:
    LogPulseError (base)
    ├── ConfigError
    ├── ValidationError
    ├── NotFoundError
    ├── ParsingError
    ├── AnalysisError
    ├── StorageError
    └── AIEngineError
        ├── AIEngineTimeoutError
        └── AIEngineUnavailableError
"""

from __future__ import annotations


class LogPulseError(Exception):
    """Exceção base do LogPulse IA.

    Todas as exceções customizadas do sistema herdam desta classe,
    permitindo capturar qualquer erro do domínio com um único handler.
    """


class ConfigError(LogPulseError):
    """Erro de configuração (logpulse.toml inválido, variável de ambiente ausente).

    Lançada durante a inicialização quando a configuração do sistema
    está ausente, malformada ou contém valores inválidos.
    """


class ValidationError(LogPulseError):
    """Erro de validação de dados de entrada.

    Lançada quando os dados fornecidos pelo usuário não atendem
    aos critérios de validação (extensão de arquivo inválida,
    conteúdo vazio, tamanho excedido, etc.).
    """


class NotFoundError(LogPulseError):
    """Recurso não encontrado no sistema.

    Lançada quando uma operação de busca por ID não encontra
    o registro solicitado no banco de dados.
    """


class AIEngineError(LogPulseError):
    """Erro ao comunicar com o motor de IA (Ollama, OpenAI, etc.).

    Subclasse base para erros relacionados à integração com LLMs.
    """


class AIEngineTimeoutError(AIEngineError):
    """Timeout esgotado após todas as tentativas de chamada ao LLM.

    Lançada quando o AIEngine esgota as 3 tentativas com backoff
    exponencial sem obter resposta dentro do limite de 30 segundos.
    """


class AIEngineUnavailableError(AIEngineError):
    """Motor de IA indisponível (serviço não está em execução).

    Lançada quando não é possível estabelecer conexão com o Ollama
    na porta 11434 antes de processar a requisição.
    """


class ParsingError(LogPulseError):
    """Erro ao parsear conteúdo de log.

    Lançada quando o parser não consegue processar o conteúdo
    fornecido, mesmo após tentativas de fallback.
    """


class AnalysisError(LogPulseError):
    """Erro durante a análise de anomalias.

    Lançada quando o Analyzer encontra um estado inválido ou
    inconsistente durante o processamento do LogStream.
    """


class StorageError(LogPulseError):
    """Erro ao persistir ou recuperar dados do SQLite.

    Lançada quando operações de leitura, escrita ou deleção
    no banco de dados falham de forma irrecuperável.
    """
