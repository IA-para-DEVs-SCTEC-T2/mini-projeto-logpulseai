---
inclusion: always
---

# Estrutura e Contribuição — LogPulse IA

## Estrutura de Pastas

```
logpulse-ia/
├── src/          # Código-fonte principal
├── tests/        # Testes automatizados
├── logs/         # Arquivos de log para testes
└── docs/         # Documentação adicional
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

### Comandos
```bash

## Commits Semânticos

**Padrão:** `<tipo>: <descrição>`

**Tipos:** `feat`, `fix`, `docs`, `refactor`

**Exemplos:**
```bash
git commit -m "feat: adiciona suporte a logs .gz"
git commit -m "fix: corrige parser JSON"
git commit -m "docs: atualiza README"
```
