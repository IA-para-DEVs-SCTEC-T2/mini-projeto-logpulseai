# Exemplo de Uso do Logging Estruturado

## Configuração Inicial

O logging é configurado automaticamente ao iniciar a aplicação em `src/main.py`:

```python
from src.core.logging import configure_logging, get_logger

# Configura logging estruturado
configure_logging(log_level="INFO", log_file="logpulse.log")
logger = get_logger(__name__)
```

## Parâmetros de Configuração

- **log_level**: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **log_file**: Caminho do arquivo de log (padrão: "logpulse.log")
- **max_bytes**: Tamanho máximo do arquivo antes da rotação (padrão: 10MB)
- **backup_count**: Número de arquivos de backup a manter (padrão: 5)

## Uso em Componentes

### Parser

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

def parse(self, raw_content: str) -> List[LogEntry]:
    logger.info("Iniciando parsing de log", content_length=len(raw_content))
    
    # ... processamento ...
    
    logger.info(
        "Parsing concluído",
        total_lines=total_lines,
        entries_parsed=len(entries),
        errors=errors,
        templates_extracted=len(self._templates)
    )
```

### Analyzer

```python
logger.info(
    "analysis_started",
    total_entries=len(entries),
    total_templates=len(templates)
)

if spikes:
    logger.warning(
        "spikes_detected",
        spike_count=len(spikes),
        spikes=[
            {
                "start_time": spike.start_time.isoformat(),
                "end_time": spike.end_time.isoformat(),
                "error_count": spike.error_count
            }
            for spike in spikes
        ]
    )
```

### AIEngine

```python
logger.info(
    "diagnosis_started",
    model=self._model,
    total_entries=len(sample_entries),
    error_count=analysis.error_count
)

logger.warning(
    "ollama_request_failed",
    attempt=attempt,
    max_retries=_MAX_RETRIES,
    error_type=type(exc).__name__,
    will_retry=attempt < _MAX_RETRIES
)
```

### Repository

```python
logger.info(
    "repository_create_started",
    log_id=log_id,
    content_length=len(content),
    total_entries=analysis.total_entries
)

logger.info("repository_create_completed", log_id=log_id)
```

### API (Middleware)

```python
logger.info(
    "request_started",
    method=request.method,
    path=request.url.path,
    client_host=request.client.host if request.client else None,
)

logger.info(
    "request_completed",
    method=request.method,
    path=request.url.path,
    status_code=response.status_code,
    duration_ms=round(duration_ms, 2),
)
```

## Níveis de Log

| Nível    | Quando usar                                      |
|----------|--------------------------------------------------|
| DEBUG    | Detalhes de parsing, decisões internas           |
| INFO     | Início/fim de análise, arquivos processados      |
| WARNING  | Linhas não parseadas, configuração faltando      |
| ERROR    | Falha ao ler arquivo, erro de API               |
| CRITICAL | Erro irrecuperável (corrupção de dados, OOM)    |

## Formato de Saída

Os logs são gerados em formato JSON estruturado:

```json
{
  "event": "analysis_started",
  "timestamp": "2024-01-15T10:00:00.123456Z",
  "level": "info",
  "logger": "src.analyzer.detector",
  "total_entries": 120,
  "total_templates": 15
}
```

## Rotação de Logs

Os arquivos de log são automaticamente rotacionados quando atingem 10MB:

- `logpulse.log` - Arquivo atual
- `logpulse.log.1` - Backup mais recente
- `logpulse.log.2` - Segundo backup
- `logpulse.log.3` - Terceiro backup
- `logpulse.log.4` - Quarto backup
- `logpulse.log.5` - Backup mais antigo

## Boas Práticas

1. **Use nomes descritivos para eventos**: `analysis_started`, `spike_detected`, `request_completed`
2. **Inclua contexto relevante**: IDs, contadores, timestamps
3. **Não exponha dados sensíveis**: Evite logar senhas, tokens, dados pessoais
4. **Use o nível apropriado**: INFO para operações normais, WARNING para situações anormais mas recuperáveis
5. **Seja consistente**: Use o mesmo formato de evento em todo o código

## Exemplo Completo

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

def process_log_file(file_path: str) -> None:
    logger.info("processing_started", file_path=file_path)
    
    try:
        # Processamento
        entries = parse_file(file_path)
        logger.debug("parsing_completed", entries_count=len(entries))
        
        analysis = analyze(entries)
        logger.info(
            "analysis_completed",
            error_count=analysis.error_count,
            spike_count=len(analysis.spikes)
        )
        
    except FileNotFoundError as exc:
        logger.error(
            "file_not_found",
            file_path=file_path,
            error=str(exc)
        )
        raise
    
    except Exception as exc:
        logger.critical(
            "unexpected_error",
            file_path=file_path,
            error_type=type(exc).__name__,
            error=str(exc)
        )
        raise
    
    finally:
        logger.info("processing_finished", file_path=file_path)
```
