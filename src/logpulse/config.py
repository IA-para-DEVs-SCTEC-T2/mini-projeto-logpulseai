"""Carregamento de configuração do logpulse.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path


_DEFAULT_CONFIG: dict[str, object] = {
    "ai": {"model": "gpt-4o"},
    "parser": {"format": "auto"},
}


def load_config(path: Path | None = None) -> dict[str, object]:
    """
    Carrega configuração do logpulse.toml.

    Busca no diretório atual e em ~/.config/logpulse/logpulse.toml.
    Retorna configuração padrão se nenhum arquivo for encontrado.
    """
    candidates = [
        path,
        Path("logpulse.toml"),
        Path.home() / ".config" / "logpulse" / "logpulse.toml",
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            with open(candidate, "rb") as f:
                return tomllib.load(f)

    return dict(_DEFAULT_CONFIG)
