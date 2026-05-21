"""Carregamento e validação de configuração do LogPulse IA via arquivo TOML.

.. deprecated::
    Este módulo é legado e não é utilizado pela aplicação FastAPI.
    A configuração ativa da aplicação está em :mod:`src.core.config`,
    que usa ``pydantic-settings`` com variáveis de ambiente prefixadas
    por ``LOGPULSE_``.

    Este arquivo é mantido apenas para compatibilidade com testes existentes
    que testam o carregamento de ``logpulse.toml``.

Precedência (maior para menor):
1. Variáveis de ambiente (LOGPULSE_API_KEY, LOGPULSE_MODEL)
2. logpulse.toml no diretório de trabalho atual
3. ~/.config/logpulse/logpulse.toml (configuração global do usuário)
4. Valores padrão hardcoded
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from src.exceptions import ConfigError

# ---------------------------------------------------------------------------
# Sub-configurações
# ---------------------------------------------------------------------------


@dataclass
class AIConfig:
    """Configuração do AI Engine (Ollama / OpenAI)."""

    model: str = "llama3"
    endpoint: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 30


@dataclass
class ParserConfig:
    """Configuração do parser de logs."""

    # auto | json | plaintext | syslog | apache
    format: str = "auto"
    custom_regex: str | None = None


@dataclass
class AnalyzerConfig:
    """Configuração do motor de detecção de anomalias."""

    spike_threshold: int = 10
    window_seconds: int = 60
    min_cluster_size: int = 3


@dataclass
class OutputConfig:
    """Configuração de saída da CLI / API."""

    format: str = "text"  # text | json
    color: bool = True


@dataclass
class AppConfig:
    """Configuração completa da aplicação."""

    ai: AIConfig = field(default_factory=AIConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    analyzer: AnalyzerConfig = field(default_factory=AnalyzerConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


# ---------------------------------------------------------------------------
# Caminhos de busca
# ---------------------------------------------------------------------------

_LOCAL_CONFIG = Path("logpulse.toml")
_USER_CONFIG = Path.home() / ".config" / "logpulse" / "logpulse.toml"


# ---------------------------------------------------------------------------
# Funções internas
# ---------------------------------------------------------------------------


def _read_toml(path: Path) -> dict[str, object]:
    """Lê e parseia um arquivo TOML.

    Args:
        path: Caminho para o arquivo .toml.

    Returns:
        Dicionário com o conteúdo do arquivo.

    Raises:
        ConfigError: Se o arquivo existir mas contiver TOML inválido.
    """
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f"Arquivo de configuração inválido: {path}\n{exc}"
        ) from exc


def _merge_dicts(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    """Mescla dois dicionários recursivamente.

    Valores de ``override`` têm precedência sobre ``base``.

    Args:
        base: Dicionário base (menor precedência).
        override: Dicionário com valores que sobrescrevem a base.

    Returns:
        Novo dicionário mesclado.
    """
    result: dict[str, object] = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)  # type: ignore[arg-type]
        else:
            result[key] = value
    return result


def _apply_env_vars(config: AppConfig) -> None:
    """Aplica variáveis de ambiente sobre a configuração carregada.

    Variáveis suportadas:
    - LOGPULSE_API_KEY  → config.ai.api_key (não armazenada no dataclass,
      usada diretamente pelo AIEngine via os.environ)
    - LOGPULSE_MODEL    → config.ai.model
    - LOGPULSE_ENDPOINT → config.ai.endpoint

    Args:
        config: Instância de AppConfig a ser modificada in-place.
    """
    if model := os.environ.get("LOGPULSE_MODEL"):
        config.ai.model = model

    if endpoint := os.environ.get("LOGPULSE_ENDPOINT"):
        config.ai.endpoint = endpoint


def _dict_to_config(data: dict[str, object]) -> AppConfig:
    """Converte um dicionário TOML em AppConfig.

    Args:
        data: Dicionário com seções [ai], [parser], [analyzer], [output].

    Returns:
        Instância de AppConfig populada.

    Raises:
        ConfigError: Se algum valor tiver tipo incompatível.
    """
    try:
        ai_data = data.get("ai", {})
        parser_data = data.get("parser", {})
        analyzer_data = data.get("analyzer", {})
        output_data = data.get("output", {})

        ai = AIConfig(**ai_data)  # type: ignore[arg-type]
        parser = ParserConfig(**parser_data)  # type: ignore[arg-type]
        analyzer = AnalyzerConfig(**analyzer_data)  # type: ignore[arg-type]
        output = OutputConfig(**output_data)  # type: ignore[arg-type]

        _validate_types(ai, analyzer)

        return AppConfig(ai=ai, parser=parser, analyzer=analyzer, output=output)

    except TypeError as exc:
        raise ConfigError(f"Valor inválido no arquivo de configuração: {exc}") from exc


def _validate_types(ai: AIConfig, analyzer: AnalyzerConfig) -> None:
    """Valida tipos dos campos numéricos após construção dos dataclasses.

    Args:
        ai: Configuração do AI Engine.
        analyzer: Configuração do Analyzer.

    Raises:
        ConfigError: Se algum campo numérico contiver tipo incompatível.
    """
    int_fields: list[tuple[str, object]] = [
        ("ai.max_tokens", ai.max_tokens),
        ("ai.timeout_seconds", ai.timeout_seconds),
        ("analyzer.spike_threshold", analyzer.spike_threshold),
        ("analyzer.window_seconds", analyzer.window_seconds),
        ("analyzer.min_cluster_size", analyzer.min_cluster_size),
    ]
    float_fields: list[tuple[str, object]] = [
        ("ai.temperature", ai.temperature),
    ]
    for name, value in int_fields:
        if not isinstance(value, int):
            raise ConfigError(
                f"Valor inválido no arquivo de configuração: '{name}' deve ser inteiro, "
                f"recebido {type(value).__name__!r}"
            )
    for name, value in float_fields:
        if not isinstance(value, (int, float)):
            raise ConfigError(
                f"Valor inválido no arquivo de configuração: '{name}' deve ser número, "
                f"recebido {type(value).__name__!r}"
            )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def load_config(
    local_path: Path | None = None,
    user_path: Path | None = None,
) -> AppConfig:
    """Carrega a configuração da aplicação respeitando a ordem de precedência.

    Ordem de precedência (maior para menor):
    1. Variáveis de ambiente (LOGPULSE_MODEL, LOGPULSE_ENDPOINT)
    2. ``local_path`` / ``logpulse.toml`` no diretório de trabalho
    3. ``user_path`` / ``~/.config/logpulse/logpulse.toml``
    4. Valores padrão dos dataclasses

    Args:
        local_path: Caminho alternativo para o arquivo de configuração local.
            Se ``None``, usa ``logpulse.toml`` no diretório de trabalho.
        user_path: Caminho alternativo para o arquivo de configuração global.
            Se ``None``, usa ``~/.config/logpulse/logpulse.toml``.

    Returns:
        Instância de AppConfig com todas as configurações mescladas.

    Raises:
        ConfigError: Se algum arquivo de configuração existir mas for inválido.

    Example:
        >>> config = load_config()
        >>> print(config.ai.model)
        'llama3'
        >>> print(config.analyzer.spike_threshold)
        10
    """
    resolved_local = local_path or _LOCAL_CONFIG
    resolved_user = user_path or _USER_CONFIG

    merged: dict[str, object] = {}

    # Camada 1: configuração global do usuário (menor precedência entre arquivos)
    if resolved_user.exists():
        user_data = _read_toml(resolved_user)
        merged = _merge_dicts(merged, user_data)

    # Camada 2: configuração local (sobrescreve global)
    if resolved_local.exists():
        local_data = _read_toml(resolved_local)
        merged = _merge_dicts(merged, local_data)

    config = _dict_to_config(merged) if merged else AppConfig()

    # Camada 3: variáveis de ambiente (maior precedência)
    _apply_env_vars(config)

    return config


def get_api_key() -> str | None:
    """Retorna a chave de API do LLM a partir da variável de ambiente.

    A variável ``LOGPULSE_API_KEY`` tem precedência sobre qualquer arquivo
    de configuração. Quando usando Ollama local, a chave não é necessária.

    Returns:
        Chave de API como string, ou ``None`` se não configurada.

    Example:
        >>> import os
        >>> os.environ["LOGPULSE_API_KEY"] = "sk-test"
        >>> get_api_key()
        'sk-test'
    """
    return os.environ.get("LOGPULSE_API_KEY")
