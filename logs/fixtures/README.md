# Fixtures de Log para Testes

Arquivos de log de exemplo utilizados para testes unitários, de integração e demonstrações.

## Arquivos Disponíveis

| Arquivo | Formato | Descrição |
|---------|---------|-----------|
| `python_traceback.log` | Plaintext | Logs com tracebacks Python multi-linha |
| `java_stacktrace.log` | Plaintext | Logs com stacktraces Java (NullPointer, IOException) |
| `go_panic.log` | Plaintext | Logs com panic/goroutine do Go |
| `spike_errors.log` | Plaintext | Cenário de spike de erros (database timeout) |
| `json_structured.log` | JSON | Logs estruturados em formato JSON (um objeto por linha) |
| `syslog_format.log` | Syslog | Logs no formato syslog (RFC 3164) |
| `mixed_severity.log` | Plaintext | Logs com todos os níveis de severidade |

## Uso em Testes

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "logs" / "fixtures"

def test_parse_python_traceback():
    content = (FIXTURES_DIR / "python_traceback.log").read_text()
    # ...
```

## Cenários Cobertos

- **Stack traces**: Python (Traceback), Java (Exception in thread), Go (panic)
- **Spikes de erro**: 10+ erros em janela de 60 segundos
- **Formatos**: Plaintext, JSON estruturado, Syslog
- **Severidades**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Casos reais**: OOM kill, connection timeout, disk full, rate limiting
