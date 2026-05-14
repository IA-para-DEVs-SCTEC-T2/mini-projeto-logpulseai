"""Hierarquia de exceções customizadas do LogPulse IA.

Define todas as exceções específicas do domínio, organizadas em uma
hierarquia que facilita o tratamento granular de erros.
"""

from __future__ import annotations


class LogPulseError(Exception):
    """Exceção base do LogPulse IA.

    Todas as exceções customizadas do sistema herdam desta classe,
    permitindo capturar qualquer erro do domínio com um único handler.
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
