---
inclusion: always
---

# Tecnologia — LogPulse IA

## Stack

- **Linguagem:** Python 3.11+
- **Gerenciador de pacotes:** `pip` com `pyproject.toml`
- **CLI:** `typer` ou `click`
- **Testes:** `pytest` com property-based testing via `hypothesis`
- **Configuração:** `tomllib` (stdlib Python 3.11+)
- **Qualidade de código:** `mypy` (strict), `black`, `isort`, `ruff`

## Convenções de Código

- Tipagem estática com `mypy` (strict mode) — sem `Any` sem justificativa
- Formatação com `black` e `isort`
- Linting com `ruff`
- Docstrings em português para funções e classes públicas
- Nomes de variáveis e funções em inglês (`snake_case`)
- Classes em `PascalCase`
- Testes espelham a estrutura de `src/` dentro de `tests/`
