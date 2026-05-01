---
inclusion: always
---

# Estrutura e Contribuição — LogPulse IA

## Estrutura de Pastas

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

## GitHub Flow

### Branches
- `main` → protegida, sempre estável
- `feature/*` → novas funcionalidades
- `bugfix/*` → correções de bugs

### Fluxo
```
main → feature/nome → PR (1 aprovação) → merge → main
main → bugfix/nome → PR (1 aprovação) → merge → main
```

## Commits Semânticos

**Padrão:** `<tipo>: <descrição>`

**Tipos:** `feat`, `fix`, `docs`, `refactor`

**Exemplos:**
```bash
git commit -m "feat: adiciona nova funcionalidade"
git commit -m "fix: corrige bug"
git commit -m "docs: atualiza documentação"
```
