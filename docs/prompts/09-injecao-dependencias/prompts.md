# Prompts — Injeção de Dependências FastAPI

## Tarefa

**Issue #291** — Configurar injeção de dependências do FastAPI

## Prompt Utilizado

```
Implementar injeção de dependências
Tarefa Principal: #291
Descricao: Configurar injeção de dependências do FastAPI
Criterios de Aceitacao:
Estimativa: 1h
Requisitos: RNF-05
Criado automaticamente via script
implemente a tarefa, crie a branch e commite conforme estabelecido em .github,
documente os prompts utilizados para a construção da tarefa em docs/prompts
```

## Decisões Técnicas

### Estrutura Criada

```
src/core/
├── __init__.py          # Exporta API pública do módulo core
├── config.py            # Settings via pydantic-settings (env vars)
└── dependencies.py      # Funções de DI para FastAPI Depends()

src/api/
├── __init__.py
├── app.py               # Factory create_app() com lifespan
└── v1/
    ├── __init__.py
    ├── router.py        # Router agregador v1
    └── logs.py          # Endpoints CRUD com DI
```

### Padrões Aplicados

1. **pydantic-settings** para configuração centralizada com prefixo `LOGPULSE_`
2. **Factory pattern** (`create_app()`) para facilitar testes
3. **Dependency Inversion** — endpoints dependem de abstrações (`LogParser`, `LogAnalyzer`, `AIEngine`, `LogRepository`)
4. **AsyncGenerator** para dependências que requerem inicialização (repository)
5. **lru_cache** no `get_settings()` para singleton de configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LOGPULSE_OLLAMA_BASE_URL` | `http://localhost:11434/v1` | URL do Ollama |
| `LOGPULSE_OLLAMA_MODEL` | `llama3` | Modelo LLM |
| `LOGPULSE_DATABASE_URL` | `logpulse.db` | Caminho do SQLite |
| `LOGPULSE_API_DEBUG` | `false` | Modo debug |

### Testes

- `tests/core/test_config.py` — 5 testes (Settings, get_settings)
- `tests/core/test_dependencies.py` — 13 testes (get_parser, get_analyzer, get_ai_engine, get_repository)
- `tests/api/test_app.py` — 4 testes (create_app, routers, OpenAPI)

**Total: 22 testes adicionados, todos passando.**

## Resultado

- Branch: `feature/injecao-dependencias`
- Commit: `feat: configura injeção de dependências do FastAPI`
