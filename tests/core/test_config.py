"""Testes para o módulo de configuração do LogPulse IA."""

from __future__ import annotations

import pytest

from src.core.config import Settings, get_settings


class TestSettings:
    """Testes para a classe Settings."""

    def test_default_values(self) -> None:
        """Verifica que os valores padrão são carregados corretamente."""
        settings = Settings()

        assert settings.ollama_base_url == "http://localhost:11434/v1"
        assert settings.ollama_model == "llama3"
        assert settings.ollama_timeout == 30
        assert settings.ollama_max_retries == 3
        assert settings.database_url == "logpulse.db"
        assert settings.drain_depth == 4
        assert settings.drain_sim_th == 0.4
        assert settings.spike_threshold == 10
        assert settings.spike_window_seconds == 60
        assert settings.api_title == "LogPulse IA"
        assert settings.api_version == "0.1.0"
        assert settings.api_debug is False

    def test_custom_values_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifica que variáveis de ambiente com prefixo LOGPULSE_ são lidas."""
        monkeypatch.setenv("LOGPULSE_OLLAMA_MODEL", "llama3.1")
        monkeypatch.setenv("LOGPULSE_DATABASE_URL", ":memory:")
        monkeypatch.setenv("LOGPULSE_API_DEBUG", "true")

        settings = Settings()

        assert settings.ollama_model == "llama3.1"
        assert settings.database_url == ":memory:"
        assert settings.api_debug is True

    def test_extra_env_vars_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifica que variáveis extras não causam erro (extra='ignore')."""
        monkeypatch.setenv("LOGPULSE_UNKNOWN_VAR", "value")

        # Não deve lançar exceção
        settings = Settings()
        assert settings.ollama_model == "llama3"


class TestGetSettings:
    """Testes para a função get_settings."""

    def test_returns_settings_instance(self) -> None:
        """Verifica que get_settings retorna instância de Settings."""
        # Limpa cache para teste isolado
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_singleton_behavior(self) -> None:
        """Verifica que get_settings retorna a mesma instância (cache)."""
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
