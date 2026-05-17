# Prompts — Implementar Normalização de Severidade

## Tarefa

**Implementar normalização de severidade**

- **Issue**: #263
- **Requisitos**: RF-03.4, RF-03.6
- **Estimativa**: 1h

## Descrição

Normalizar aliases de severidade para valores padrão (SeverityLevel enum).

## Status

✅ Implementado em `src/parsers/normalizer.py` com cobertura completa de testes.

## Mapeamento de Aliases

| Alias (case-insensitive) | SeverityLevel |
|--------------------------|---------------|
| trace                    | DEBUG         |
| debug                    | DEBUG         |
| info, information        | INFO          |
| warn, warning            | WARNING       |
| err, error               | ERROR         |
| fatal, critical, crit    | CRITICAL      |
| emerg, alert             | CRITICAL      |

## Comportamento

- Input `None` ou vazio → `SeverityLevel.INFO` com `inferred=True`
- Alias reconhecido → nível correspondente com `inferred=False`
- Match parcial (ex: `"[ERROR]"` contém `"error"`) → nível correspondente
- Alias desconhecido → `SeverityLevel.INFO` com `inferred=True`
- Case-insensitive: `"WARN"`, `"warn"`, `"Warn"` → todos `WARNING`

## Prompts Utilizados

### Prompt 1 — Documentação

```
Documentar a implementação existente de normalização de severidade em
src/parsers/normalizer.py, incluindo tabela de aliases, comportamento
de fallback e property-based tests.
```

## Arquivos Relevantes

- `src/parsers/normalizer.py` — Implementação (função `normalize_severity`)
- `tests/parsers/test_normalizer.py` — 15+ testes unitários + PBT

## Resultado dos Testes

- Testes de normalizer: ✅ PASSED
