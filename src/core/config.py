"""Configuração centralizada do LogPulse IA via pydantic-settings.

Carrega variáveis de ambiente com prefixo LOGPULSE_ e fornece
valores padrão sensatos para execução local com Ollama.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais da aplicação.

    Valores são carregados de variáveis de ambiente com prefixo LOGPULSE_
    ou do arquivo .env na raiz do projeto.

    Example:
        >>> settings = Settings()
        >>> print(settings.ollama_base_url)
        'http://localhost:11434/v1'
    """

    # --- AI / Ollama ---
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 120
    ollama_max_retries: int = 3

    # --- Database ---
    database_url: str = "logpulse.db"

    # --- Parser ---
    drain_depth: int = 4
    drain_sim_th: float = 0.4

    # --- Analyzer ---
    spike_threshold: int = 10
    spike_window_seconds: int = 60

    # --- API ---
    api_title: str = "LogPulse IA"
    api_version: str = "0.1.0"
    api_debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="LOGPULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna instância singleton das configurações.

    Usa lru_cache para garantir que apenas uma instância é criada
    durante o ciclo de vida da aplicação.

    Returns:
        Instância de Settings com valores carregados do ambiente.
    """
    return Settings()
