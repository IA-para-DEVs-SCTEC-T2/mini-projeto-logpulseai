# Prompts — Criar Modelos Base (SeverityLevel, LogEntry, LogTemplate)

## Tarefa

**Criar modelos base (SeverityLevel, LogEntry, LogTemplate)**

- **Issue**: #259
- **Requisitos**: RF-03.1, RF-03.4
- **Estimativa**: 1h

## Descrição

Criar modelos Pydantic fundamentais para representar logs e templates.

## Status

✅ Modelos já implementados em `src/models/schemas.py` com cobertura de testes
completa em `tests/models/test_schemas.py` (incluindo property-based testing).

## Modelos Implementados

### SeverityLevel (Enum)
- DEBUG, INFO, WARNING, ERROR, CRITICAL
- Herda de `str, Enum` para serialização JSON nativa

### LogEntry (BaseModel)
- `id`: UUID auto-gerado
- `raw_content`: Conteúdo bruto (min_length=1, strip automático)
- `template_id`: ID do template Drain3 (opcional)
- `severity`: SeverityLevel (default: INFO)
- `timestamp`: datetime (opcional)
- `message`: Mensagem principal
- `level_inferred`: Flag de inferência de nível
- `timestamp_inferred`: Flag de inferência de timestamp

### LogTemplate (BaseModel)
- `template_id`: Identificador único
- `pattern`: Padrão com placeholders
- `occurrences`: Contagem (ge=0)
- `sample_messages`: Até 5 amostras (validado por field_validator)

## Prompts Utilizados

### Prompt 1 — Documentação da tarefa existente

```
Documentar os modelos base já implementados em src/models/schemas.py,
incluindo SeverityLevel, LogEntry e LogTemplate. Verificar que os testes
existentes cobrem os critérios de aceitação da tarefa #259.
```

## Arquivos Relevantes

- `src/models/schemas.py` — Modelos Pydantic (já existente)
- `src/models/__init__.py` — Exportações do módulo
- `tests/models/test_schemas.py` — Testes unitários + property-based (já existente)

## Resultado dos Testes

- Testes de modelos: ✅ PASSED (verificado via pytest)
