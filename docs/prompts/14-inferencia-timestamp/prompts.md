# Prompts — Implementar Inferência de Timestamp

## Tarefa

**Implementar inferência de timestamp**

- **Issue**: #263
- **Requisitos**: RF-03.5
- **Estimativa**: 1-2h

## Descrição

Detectar e parsear timestamps em múltiplos formatos.

## Status

✅ Implementado em `src/parsers/normalizer.py` com cobertura completa de testes.

## Formatos Suportados

1. **ISO 8601 / RFC 3339**: `2024-01-15T10:00:00Z`, `2024-01-15T10:00:00+00:00`
2. **Syslog RFC 3164**: `Jan 15 10:00:00`
3. **Formato com barra**: `2024/01/15 10:00:00`
4. **Formato com traço sem T**: `2024-01-15 10:00:00`

## Comportamento de Inferência

- Se timestamp não encontrado → usa `datetime.now(UTC)` com `inferred=True`
- Se timestamp encontrado → parseia e retorna com `inferred=False`
- Resultado sempre tem timezone (UTC se não especificado)

## Funções Implementadas

- `parse_timestamp(raw_ts)` → `(datetime | None, inferred: bool)`
- `extract_timestamp_from_line(line)` → `(datetime | None, inferred: bool, remaining: str)`

## Prompts Utilizados

### Prompt 1 — Documentação

```
Documentar a implementação existente de inferência de timestamp em
src/parsers/normalizer.py, incluindo formatos suportados, comportamento
de fallback e property-based tests existentes.
```

## Arquivos Relevantes

- `src/parsers/normalizer.py` — Implementação (já existente)
- `tests/parsers/test_normalizer.py` — Testes unitários + PBT (já existente)

## Resultado dos Testes

- Testes de normalizer: ✅ PASSED
