"""Testes do módulo de configuração (src/config.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import (
    AIConfig,
    AnalyzerConfig,
    AppConfig,
    OutputConfig,
    ParserConfig,
    get_api_key,
    load_config,
)
from src.exceptions import ConfigError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def local_toml(tmp_path: Path) -> Path:
    """Cria um logpulse.toml local válido em tmp_path."""
    config_file = tmp_path / "logpulse.toml"
    config_file.write_text(
        """
[ai]
model = "llama3"
endpoint = "http://localhost:11434"
temperature = 0.5
max_tokens = 500
timeout_seconds = 15

[parser]
format = "json"

[analyzer]
spike_threshold = 5
window_seconds = 30
min_cluster_size = 2

[output]
format = "json"
color = false
""",
        encoding="utf-8",
    )
    return config_file


@pytest.fixture()
def user_toml(tmp_path: Path) -> Path:
    """Cria um logpulse.toml global do usuário em tmp_path."""
    config_file = tmp_path / "user_logpulse.toml"
    config_file.write_text(
        """
[ai]
model = "gpt-4o"
temperature = 0.9
""",
        encoding="utf-8",
    )
    return config_file


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove variáveis de ambiente do LogPulse antes de cada teste."""
    monkeypatch.delenv("LOGPULSE_API_KEY", raising=False)
    monkeypatch.delenv("LOGPULSE_MODEL", raising=False)
    monkeypatch.delenv("LOGPULSE_ENDPOINT", raising=False)


# ---------------------------------------------------------------------------
# Testes: valores padrão
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    """Testa que AppConfig retorna os valores padrão corretos."""

    def test_ai_defaults(self) -> None:
        """Verifica valores padrão da seção [ai]."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert config.ai.model == "llama3"
        assert config.ai.endpoint == "http://localhost:11434"
        assert config.ai.temperature == 0.7
        assert config.ai.max_tokens == 1000
        assert config.ai.timeout_seconds == 30

    def test_parser_defaults(self) -> None:
        """Verifica valores padrão da seção [parser]."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert config.parser.format == "auto"
        assert config.parser.custom_regex is None

    def test_analyzer_defaults(self) -> None:
        """Verifica valores padrão da seção [analyzer]."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert config.analyzer.spike_threshold == 10
        assert config.analyzer.window_seconds == 60
        assert config.analyzer.min_cluster_size == 3

    def test_output_defaults(self) -> None:
        """Verifica valores padrão da seção [output]."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert config.output.format == "text"
        assert config.output.color is True

    def test_returns_app_config_instance(self) -> None:
        """Verifica que load_config retorna uma instância de AppConfig."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert isinstance(config, AppConfig)
        assert isinstance(config.ai, AIConfig)
        assert isinstance(config.parser, ParserConfig)
        assert isinstance(config.analyzer, AnalyzerConfig)
        assert isinstance(config.output, OutputConfig)


# ---------------------------------------------------------------------------
# Testes: carregamento de arquivo local
# ---------------------------------------------------------------------------


class TestLocalConfig:
    """Testa carregamento do arquivo logpulse.toml local."""

    def test_loads_local_file(self, local_toml: Path) -> None:
        """Verifica que valores do arquivo local são carregados corretamente."""
        config = load_config(local_path=local_toml, user_path=Path("nonexistent.toml"))
        assert config.ai.model == "llama3"
        assert config.ai.temperature == 0.5
        assert config.ai.max_tokens == 500
        assert config.ai.timeout_seconds == 15

    def test_loads_parser_section(self, local_toml: Path) -> None:
        """Verifica que a seção [parser] é carregada do arquivo local."""
        config = load_config(local_path=local_toml, user_path=Path("nonexistent.toml"))
        assert config.parser.format == "json"

    def test_loads_analyzer_section(self, local_toml: Path) -> None:
        """Verifica que a seção [analyzer] é carregada do arquivo local."""
        config = load_config(local_path=local_toml, user_path=Path("nonexistent.toml"))
        assert config.analyzer.spike_threshold == 5
        assert config.analyzer.window_seconds == 30
        assert config.analyzer.min_cluster_size == 2

    def test_loads_output_section(self, local_toml: Path) -> None:
        """Verifica que a seção [output] é carregada do arquivo local."""
        config = load_config(local_path=local_toml, user_path=Path("nonexistent.toml"))
        assert config.output.format == "json"
        assert config.output.color is False

    def test_ignores_missing_local_file(self) -> None:
        """Verifica que arquivo local ausente não causa erro."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert config.ai.model == "llama3"  # valor padrão


# ---------------------------------------------------------------------------
# Testes: precedência entre arquivos
# ---------------------------------------------------------------------------


class TestConfigPrecedence:
    """Testa a ordem de precedência entre arquivo local e global."""

    def test_local_overrides_user(self, local_toml: Path, user_toml: Path) -> None:
        """Arquivo local tem precedência sobre o global do usuário."""
        # user_toml define model = "gpt-4o", local_toml define model = "llama3"
        config = load_config(local_path=local_toml, user_path=user_toml)
        assert config.ai.model == "llama3"

    def test_user_fills_missing_local_keys(self, local_toml: Path, user_toml: Path) -> None:
        """Chaves ausentes no local são preenchidas pelo global."""
        # user_toml define temperature = 0.9, local_toml define temperature = 0.5
        config = load_config(local_path=local_toml, user_path=user_toml)
        # local tem precedência: temperature = 0.5
        assert config.ai.temperature == 0.5

    def test_user_only_when_no_local(self, user_toml: Path) -> None:
        """Quando não há arquivo local, usa o global do usuário."""
        config = load_config(local_path=Path("nonexistent.toml"), user_path=user_toml)
        assert config.ai.model == "gpt-4o"
        assert config.ai.temperature == 0.9


# ---------------------------------------------------------------------------
# Testes: variáveis de ambiente
# ---------------------------------------------------------------------------


class TestEnvVarPrecedence:
    """Testa que variáveis de ambiente sobrescrevem arquivos de configuração."""

    def test_env_model_overrides_file(
        self, local_toml: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """LOGPULSE_MODEL tem precedência sobre o arquivo de configuração."""
        monkeypatch.setenv("LOGPULSE_MODEL", "gpt-4o-mini")
        config = load_config(local_path=local_toml, user_path=Path("nonexistent.toml"))
        assert config.ai.model == "gpt-4o-mini"

    def test_env_endpoint_overrides_file(
        self, local_toml: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """LOGPULSE_ENDPOINT tem precedência sobre o arquivo de configuração."""
        monkeypatch.setenv("LOGPULSE_ENDPOINT", "http://remote-ollama:11434")
        config = load_config(local_path=local_toml, user_path=Path("nonexistent.toml"))
        assert config.ai.endpoint == "http://remote-ollama:11434"

    def test_env_model_overrides_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LOGPULSE_MODEL tem precedência mesmo sem arquivo de configuração."""
        monkeypatch.setenv("LOGPULSE_MODEL", "llama3:70b")
        config = load_config(local_path=Path("nonexistent.toml"), user_path=Path("nonexistent.toml"))
        assert config.ai.model == "llama3:70b"


# ---------------------------------------------------------------------------
# Testes: get_api_key
# ---------------------------------------------------------------------------


class TestGetApiKey:
    """Testa a função get_api_key."""

    def test_returns_none_when_not_set(self) -> None:
        """Retorna None quando LOGPULSE_API_KEY não está definida."""
        assert get_api_key() is None

    def test_returns_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Retorna o valor de LOGPULSE_API_KEY quando definida."""
        monkeypatch.setenv("LOGPULSE_API_KEY", "sk-test-key-123")
        assert get_api_key() == "sk-test-key-123"

    def test_returns_empty_string_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Retorna string vazia quando LOGPULSE_API_KEY está vazia."""
        monkeypatch.setenv("LOGPULSE_API_KEY", "")
        assert get_api_key() == ""


# ---------------------------------------------------------------------------
# Testes: erros de configuração
# ---------------------------------------------------------------------------


class TestConfigErrors:
    """Testa tratamento de erros no carregamento de configuração."""

    def test_raises_config_error_on_invalid_toml(self, tmp_path: Path) -> None:
        """ConfigError é levantado para TOML inválido."""
        invalid_toml = tmp_path / "logpulse.toml"
        invalid_toml.write_text("chave_sem_valor = \n[seção inválida", encoding="utf-8")

        with pytest.raises(ConfigError, match="Arquivo de configuração inválido"):
            load_config(local_path=invalid_toml, user_path=Path("nonexistent.toml"))

    def test_raises_config_error_on_invalid_field_type(self, tmp_path: Path) -> None:
        """ConfigError é levantado para campo com tipo incompatível."""
        bad_toml = tmp_path / "logpulse.toml"
        # spike_threshold espera int, mas recebe array — TypeError no dataclass
        bad_toml.write_text(
            "[analyzer]\nspike_threshold = [1, 2, 3]\n",
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="Valor inválido"):
            load_config(local_path=bad_toml, user_path=Path("nonexistent.toml"))

    def test_raises_config_error_on_unknown_field(self, tmp_path: Path) -> None:
        """ConfigError é levantado para campo desconhecido no dataclass."""
        bad_toml = tmp_path / "logpulse.toml"
        bad_toml.write_text(
            "[ai]\ncampo_inexistente = 'valor'\n",
            encoding="utf-8",
        )

        with pytest.raises(ConfigError, match="Valor inválido"):
            load_config(local_path=bad_toml, user_path=Path("nonexistent.toml"))
