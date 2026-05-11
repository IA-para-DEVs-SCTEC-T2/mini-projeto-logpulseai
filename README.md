# LogPulse IA

> Investigue problemas rapidamente através dos seus logs.

## Objetivo

O **LogPulse IA** é uma ferramenta de linha de comando e biblioteca Python para ingestão, análise e investigação inteligente de logs. Com suporte a IA, permite identificar a causa raiz de incidentes de forma rápida, reduzindo o MTTR (Mean Time To Resolution) em ambientes de produção.

## Estrutura do Projeto

```
mini-projeto-logpulse-ia/
├── .github/              # Workflows de CI/CD e configurações do GitHub
├── .kiro/                # Configurações do Kiro (specs, steering rules)
├── docs/                 # Documentação adicional
├── logs/                 # Arquivos de log para testes e exemplos
├── src/                  # Código-fonte principal
├── tests/                # Testes automatizados
└── README.md
```

## Tecnologias

- **Linguagem:** Python 3.11+
- **Gerenciador de pacotes:** `pip` com `pyproject.toml`
- **Testes:** `pytest` com property-based testing via `hypothesis`
- **Qualidade de código:** `mypy` (strict), `black`, `isort`, `ruff`

## GitHub Flow

**Branches:**
- `main` → protegida, sempre estável
- `feature/*` → novas funcionalidades
- `bugfix/*` → correções de bugs

**Fluxo:**
```
main → feature/nome → PR (1 aprovação) → merge → main
main → bugfix/nome → PR (1 aprovação) → merge → main
```

**Commits semânticos:**
- `feat:` para novas funcionalidades
- `fix:` para correções
- `docs:` para documentação
- `refactor:` para refatorações

## Status

🚧 Em desenvolvimento ativo

