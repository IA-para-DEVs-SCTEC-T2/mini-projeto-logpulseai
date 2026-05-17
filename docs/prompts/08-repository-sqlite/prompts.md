# Task 08 — Camada de Persistência: Repository SQLite

## Contexto

Implementação da camada de persistência do LogPulse IA usando SQLite com operações assíncronas via `aiosqlite`. Esta tarefa cria a interface abstrata `LogRepository` e a implementação concreta `SQLiteLogRepository`.

## Arquivos Criados

| Arquivo | Descrição |
|---|---|
| `src/exceptions.py` | Hierarquia de exceções do domínio (LogPulseError, StorageError, etc.) |
| `src/repository/__init__.py` | Exporta LogRepository e SQLiteLogRepository |
| `src/repository/base.py` | Interface abstrata LogRepository com métodos CRUD assíncronos |
| `src/repository/sqlite_repository.py` | Implementação SQLite com aiosqlite |
| `tests/repository/__init__.py` | Pacote de testes do repositório |
| `tests/repository/test_sqlite_repository.py` | 18 testes cobrindo todos os critérios de aceitação |

## Decisões de Design

### Interface Abstrata (base.py)

Usa `ABC` e `@abstractmethod` para garantir que implementações concretas forneçam todos os métodos CRUD. A interface depende apenas dos modelos do domínio (`AnalysisResult`, `AIDiagnosis`, `LogAnalysisResponse`), sem acoplamento a detalhes de infraestrutura.

### Serialização JSON

Os modelos Pydantic são serializados com `.model_dump_json()` e desserializados com `.model_validate_json()`, aproveitando a validação nativa do Pydantic na leitura.

### Transações Atômicas

Usa o context manager `async with conn:` do aiosqlite, que garante `COMMIT` automático em caso de sucesso e `ROLLBACK` em caso de exceção. Erros do aiosqlite são capturados e relançados como `StorageError`.

### Índice em created_at

O índice `idx_logs_created_at` é criado na inicialização para otimizar as queries de listagem paginada com `ORDER BY created_at DESC`.

### Timezone UTC

Todos os timestamps são armazenados em ISO 8601 com timezone UTC. Na leitura, timestamps sem timezone recebem `tzinfo=timezone.utc` para garantir consistência.

## Prompts Utilizados

### Prompt Principal

```
Criar camada de persistência com SQLite para armazenar logs analisados.

Requisitos:
- Interface abstrata LogRepository com métodos CRUD assíncronos
- SQLiteLogRepository com schema: logs(id, content, analysis_result, ai_diagnosis, created_at)
- Índice em created_at para paginação eficiente
- Operações CRUD assíncronas com aiosqlite
- Serialização de AnalysisResult e AIDiagnosis como JSON
- Transações atômicas com rollback em caso de falha
```

### Resultado

Todos os 18 testes novos passam, e os 216 testes existentes continuam passando.
