# Prompts — Timeout e Retry com Backoff Exponencial

## Tarefa

**Implementar timeout e retry com backoff exponencial**

- **Issue**: #273
- **Requisitos**: RF-05.7, RNF-08
- **Estimativa**: 2h

## Descrição

Adicionar resiliência com timeout e retry reutilizável por qualquer componente.

## Prompts Utilizados

### Prompt 1 — Módulo de retry reutilizável

```
Criar src/core/retry.py com:
- calculate_backoff_delay(attempt, base_delay, multiplier, max_delay, jitter)
  Calcula delay com backoff exponencial e jitter para evitar thundering herd.
- retry_with_backoff(func, max_retries, retryable_exceptions, ...)
  Executa função com retry, backoff exponencial e callback on_retry.

Constantes padrão:
- MAX_RETRIES = 3
- BASE_DELAY = 1.0s
- MAX_DELAY = 30.0s
- MULTIPLIER = 2.0
- JITTER = 0.1 (10%)
```

### Prompt 2 — Testes unitários

```
Criar tests/core/test_retry.py com:
- TestCalculateBackoffDelay: delay base, exponencial, max_delay cap, jitter, customização
- TestRetryWithBackoff: sucesso 1ª tentativa, sucesso 2ª, falha total,
  exceção não-retryable, callback on_retry, delays exponenciais, max_retries=1
Usar unittest.mock.patch para time.sleep.
```

## Arquivos Criados

- `src/core/__init__.py` — Exporta utilitários
- `src/core/retry.py` — Módulo de retry com backoff exponencial
- `tests/core/__init__.py` — Pacote de testes
- `tests/core/test_retry.py` — 16 testes unitários

## Resultado dos Testes

- 16 testes: ✅ PASSED
