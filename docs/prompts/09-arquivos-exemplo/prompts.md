# Prompts — Tarefa #299: Criar Arquivos de Exemplo

## Contexto

Criar arquivos de log de exemplo para testes e demonstrações do LogPulse IA.

## Prompt Utilizado

```
Criar arquivos de log de exemplo em logs/fixtures/ cobrindo os seguintes cenários:
- Python traceback multi-linha (ConnectionError, TypeError)
- Java stacktrace (NullPointerException, IOException com Caused by)
- Go panic com goroutines
- Spike de erros (10+ erros ERROR/CRITICAL em janela de 60s)
- Logs JSON estruturados (um objeto por linha)
- Logs formato syslog (RFC 3164)
- Logs com todos os níveis de severidade (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Cada arquivo deve representar um cenário realista de produção com timestamps,
níveis de severidade e mensagens coerentes.
```

## Resultado

7 arquivos criados em `logs/fixtures/`:
- `python_traceback.log` — Tracebacks Python com ConnectionError e TypeError
- `java_stacktrace.log` — Stacktraces Java com NullPointerException e IOException
- `go_panic.log` — Panic Go com goroutines e stack frames
- `spike_errors.log` — Spike de erros por database timeout
- `json_structured.log` — Logs JSON estruturados
- `syslog_format.log` — Logs formato syslog
- `mixed_severity.log` — Todos os níveis de severidade
