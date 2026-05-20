---
inclusion: always
---

# Tecnologia — LogPulse IA

## Stack Tecnológica

### Linguagem e Runtime

- **Python 3.11+**: Escolhido pelo ecossistema maduro de IA/ML, bibliotecas de parsing de texto e ferramentas de observabilidade.

### Gerenciamento de Dependências

- **pyproject.toml** (PEP 621): Arquivo único para metadados, dependências e configuração de ferramentas
- **pip**: Instalador de pacotes padrão
- **Versionamento de dependências**:
  - Dependências diretas: usar `~=` (compatible release) para permitir patches (ex: `fastapi~=0.111.0`)
  - Dependências de desenvolvimento: versões exatas com `==` para reprodutibilidade
  - Dependências de IA: versões mínimas com `>=` devido à rápida evolução (ex: `openai>=1.30.0`)

### Framework Web

- **FastAPI**: Framework assíncrono para a API REST com validação automática via Pydantic, geração de Swagger/ReDoc e suporte nativo a type hints.

### Parsing de Logs

- **Drain3**: Biblioteca Python para extração de templates de logs brutos. Agrupa mensagens similares substituindo valores dinâmicos por wildcards (`<*>`).
- **re** (stdlib): Expressões regulares para detecção de formato (JSON, Syslog, texto livre) e extração de timestamps.

### Integração com IA/LLM

- **openai**: Cliente oficial da API OpenAI, usado como drop-in replacement apontando para o servidor Ollama local (`http://localhost:11434/v1`).
- **Ollama** (local): Servidor de LLM local rodando o modelo `llama3.2:3b` na porta 11434.

### Persistência

- **aiosqlite**: Driver assíncrono para SQLite, usado na camada de repositório.
- **SQLite**: Banco de dados embutido, sem dependência de infraestrutura externa.

### Testes

- **pytest**: Framework de testes com fixtures, parametrização e plugins
- **pytest-asyncio**: Suporte a testes assíncronos (`async def test_*`)
- **hypothesis**: Property-based testing para validação de invariantes
- **pytest-cov**: Cobertura de código integrada ao pytest

### Configuração

- **pydantic-settings**: Carregamento de configurações via variáveis de ambiente com prefixo `LOGPULSE_` e arquivo `.env`.

### Qualidade de Código

- **mypy** (strict mode): Verificação de tipos estática
- **black**: Formatação automática de código (line length: 100)
- **isort**: Ordenação de imports (profile: black)
- **ruff**: Linter moderno e rápido

---

## Arquitetura Técnica

### Padrão Arquitetural

O sistema segue **arquitetura em camadas** com **inversão de dependências** (Dependency Inversion Principle):

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│              src/api/ (FastAPI, routers)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Services Layer                            │
│    src/services/ (LogAnalysisService, LogStorageService)    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Domain / Application Layer                     │
│   src/parsers/  │  src/analyzer/  │  src/ai/               │
│   (Drain3)      │  (AnomalyDetector) │ (OllamaAIEngine)    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                Infrastructure Layer                         │
│   src/repository/ (SQLiteLogRepository)                     │
│   src/models/     (Pydantic schemas)                        │
│   src/core/       (config, logging, dependencies)           │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline de dados:**
```
Entrada → Parser (Drain3) → LogEntry → Analyzer → AnalysisResult → AIEngine → AIDiagnosis → Repository → Resposta JSON
```

### Organização de `src/`

```
src/
├── main.py                     # Ponto de entrada alternativo (uvicorn direto)
├── exceptions.py               # Hierarquia de exceções customizadas
├── config.py                   # Módulo legado (não usado pela API — ver src/core/config.py)
├── api/
│   ├── app.py                  # Factory da aplicação FastAPI (create_app)
│   ├── health.py               # Endpoint GET /health
│   ├── middleware.py           # Exception handlers centralizados
│   ├── dependencies.py         # Injeção de dependências FastAPI (legado)
│   └── v1/
│       ├── router.py           # Agrupa routers v1
│       ├── logs.py             # Re-export de compatibilidade
│       ├── controllers/
│       │   └── logs_controller.py  # Controller MVC: valida entrada e delega aos services
│       └── routes/
│           └── logs_routes.py  # View MVC: define rotas HTTP e delega ao controller
├── services/
│   ├── log_analysis_service.py # Orquestra pipeline: Parser→Analyzer→AI→Repo
│   └── log_storage_service.py  # CRUD: get_by_id, list_logs, delete_log
├── parsers/
│   ├── base.py                 # Interface abstrata LogParser
│   ├── drain3_parser.py        # Implementação com Drain3
│   └── normalizer.py           # Normalização de severidade e timestamp
├── analyzer/
│   ├── base.py                 # Interface abstrata LogAnalyzer
│   └── detector.py             # AnomalyDetector (spikes, stack traces)
├── ai/
│   ├── base.py                 # Interface abstrata AIEngine
│   ├── ollama_engine.py        # OllamaAIEngine (OpenAI SDK → Ollama)
│   └── health_check.py         # Verificação TCP de disponibilidade do Ollama
├── models/
│   └── schemas.py              # Todos os schemas Pydantic do sistema
├── repository/
│   ├── base.py                 # Interface abstrata LogRepository
│   └── sqlite_repository.py    # SQLiteLogRepository (aiosqlite)
└── core/
    ├── config.py               # Settings via pydantic-settings (LOGPULSE_*)
    ├── logging.py              # Logging estruturado
    ├── dependencies.py         # Providers de dependências FastAPI
    └── retry.py                # Utilitário de retry com backoff exponencial
```

> **Padrão MVC na camada API:** A pasta `v1/` segue o padrão MVC completo:
> `routes/` (View) → `controllers/` (Controller) → `services/` (Model/Service)

### Princípios de Design

1. **Dependency Inversion**: Camadas superiores dependem de abstrações (ABCs), não de implementações concretas
2. **Single Responsibility**: Cada módulo tem uma responsabilidade clara e única
3. **Open/Closed**: Novos parsers, analyzers e engines podem ser adicionados sem modificar código existente
4. **Interface Segregation**: ABCs pequenas e focadas (`LogParser`, `LogAnalyzer`, `AIEngine`, `LogRepository`)

---

## Modelo de Dados Central

### Schemas Pydantic (`src/models/schemas.py`)

```python
class SeverityLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogEntry(BaseModel):
    id: str                          # UUID único
    raw_content: str                 # Linha original do log
    template_id: str | None          # ID do template Drain3
    severity: SeverityLevel          # Nível normalizado
    timestamp: datetime | None       # Timestamp extraído
    message: str                     # Mensagem principal
    level_inferred: bool             # True se nível foi inferido
    timestamp_inferred: bool         # True se timestamp foi inferido

class AnalysisResult(BaseModel):
    total_entries: int
    severity_distribution: dict[SeverityLevel, int]
    error_count: int
    warning_count: int
    spikes: list[Spike]
    stack_traces: list[str]
    templates: list[LogTemplate]
    insufficient_data: bool

class AIDiagnosis(BaseModel):
    summary: str
    probable_cause: str
    hypotheses: list[Hypothesis]     # mínimo 2
    suggested_fix: str
    confidence: float                # 0.0 a 1.0

class LogAnalysisResponse(BaseModel):
    """Resposta no estilo Datadog/Sentry."""
    id: str
    analyzed_at: datetime
    metrics: dict[str, int]          # total_logs, errors, criticals
    issues: list[Issue]              # problemas agrupados por padrão
    recommended_actions: list[str]   # ações em ordem de prioridade
    confidence: float
```

---

## Convenções de Código

### Tipagem Estática

- **mypy strict mode obrigatório**: `mypy --strict src/`
- **Sem `Any` sem justificativa**: Documentar no comentário quando inevitável
- **ABCs sobre Protocols**: Usar `ABC` para interfaces de componentes principais
- **Type hints em todas as assinaturas**: Funções, métodos, lambdas
- **Generics explícitos**: `list[str]`, `dict[str, int]`, nunca `list`, `dict`

### Tratamento de Erros

#### Hierarquia de Exceções (`src/exceptions.py`)

```python
LogPulseError               # base
├── ConfigError             # configuração inválida
├── SourceError             # erro ao ler fonte
├── ParserError             # erro em linha individual
├── ParsingError            # erro no conteúdo completo
├── ValidationError         # dados de entrada inválidos
├── NotFoundError           # recurso não encontrado
├── StorageError            # erro de banco de dados
├── AnalysisError           # erro no analyzer
├── AnalyzerError           # legado — use AnalysisError em código novo
└── AIEngineError           # erro genérico de IA
    ├── AIEngineTimeoutError    # timeout do LLM
    └── AIEngineUnavailableError # Ollama indisponível
```

#### Regras de Tratamento

1. **Fail fast em configuração**: Erros de config/setup devem abortar imediatamente
2. **Resiliente em parsing**: Linhas malformadas são logadas e ignoradas (RNF-03)
3. **Graceful degradation em IA**: Se AI falhar, retorna diagnóstico heurístico (fallback)
4. **Mensagens descritivas**: Incluir contexto (arquivo, linha, valor inválido)

### Formatação e Estilo

- **black** com `line-length = 100`
- **isort** com `profile = "black"`
- **ruff** com regras: `E`, `F`, `I`, `N`, `UP`, `RUF`

### Nomenclatura

- **Variáveis e funções**: `snake_case` em inglês
- **Classes**: `PascalCase` em inglês
- **Constantes**: `UPPER_SNAKE_CASE`
- **Módulos**: `snake_case`
- **Privado**: prefixo `_`

### Docstrings

- **Idioma**: Português para funções e classes públicas
- **Formato**: Google Style
- **Obrigatório para**: Funções públicas, classes, métodos públicos, módulos

---

## Padrões de Testes

### Estrutura de Testes

- **Espelhamento**: `tests/` espelha estrutura de `src/`
- **Nomenclatura**: `test_<módulo>.py` para cada `<módulo>.py`
- **Fixtures**: Centralizadas em `tests/conftest.py` e `conftest.py` raiz

```
tests/
├── conftest.py
├── test_config.py
├── test_exceptions.py
├── ai/
├── analyzer/
├── api/
│   └── v1/
├── core/
├── models/
├── parsers/
├── repository/
└── services/
```

### Cobertura de Código

- **Meta**: 30% de line coverage mínimo
- **Comando**: `pytest --cov=src --cov-report=html --cov-report=term`
- **CI**: Bloquear merge se cobertura cair abaixo de 30%

---

## Padrão de Configuração

### Variáveis de Ambiente (`src/core/config.py`)

Todas as configurações usam prefixo `LOGPULSE_`:

```env
LOGPULSE_OLLAMA_BASE_URL=http://localhost:11434/v1
LOGPULSE_OLLAMA_MODEL=llama3.2:3b
LOGPULSE_OLLAMA_TIMEOUT=120
LOGPULSE_DATABASE_URL=logpulse.db
LOGPULSE_DRAIN_DEPTH=4
LOGPULSE_DRAIN_SIM_TH=0.4
LOGPULSE_SPIKE_THRESHOLD=10
LOGPULSE_SPIKE_WINDOW_SECONDS=60
LOGPULSE_API_TITLE=LogPulse IA
LOGPULSE_API_VERSION=0.1.0
LOGPULSE_API_DEBUG=false
```

---

## Automações e CI

### GitHub Actions Workflows

- `branch-validation.yml`: Valida nomenclatura de branches (`feature/*`, `bugfix/*`)
- `commit-validation.yml`: Valida commits semânticos (`feat`, `fix`, `docs`, `refactor`)
- `protect-main.yml`: Bloqueia push direto na `main`
- `branch-up-to-date.yml`: Garante branch atualizada antes do merge
- `approval-gate.yml`: Exige aprovação de PR

### Bloqueio de Merge

- **Requer**: Todos os checks do CI passando (lint, types, tests, coverage ≥30%)
- **Requer**: 1 aprovação de code review
- **Requer**: Branch atualizada com `main`
