# Design — LogPulse IA

## 1. Introdução

O **LogPulse IA** é uma API REST que recebe logs brutos (stacktraces, logs de produção), analisa padrões de erro com auxílio de IA local (Ollama/LLaMA 3.2) e retorna diagnósticos estruturados com causa raiz e sugestões de correção.

Este documento descreve a arquitetura implementada, os componentes, os fluxos de dados, as integrações externas e as decisões técnicas do sistema.

---

## 2. Visão Geral da Arquitetura

O sistema segue uma arquitetura em camadas, organizada em módulos coesos dentro de `src/`. A comunicação externa ocorre exclusivamente via API REST (FastAPI), e o processamento interno é dividido entre parsing, análise, diagnóstico IA e persistência.

```
┌─────────────────────────────────────────────────────────┐
│                        Cliente                          │
│              (Swagger UI / HTTP Client)                 │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│   src/api/app.py  │  src/api/v1/routes/logs_routes.py   │
│   POST /file  │  POST /text  │  GET /  │  GET /{id}     │
│               │              │  DELETE /{id}            │
└──────┬─────────────────┬─────┴─────────────────────────┘
       │                 │
┌──────▼──────────────────▼──────────────────────────────┐
│                   Services Layer                        │
│   src/services/log_analysis_service.py                  │
│   src/services/log_storage_service.py                   │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│              Domain / Application Layer                 │
│  src/parsers/drain3_parser.py  (Drain3)                 │
│  src/analyzer/detector.py      (AnomalyDetector)        │
│  src/ai/ollama_engine.py       (OllamaAIEngine)         │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│                 Infrastructure Layer                    │
│   src/repository/sqlite_repository.py  (aiosqlite)      │
│   src/models/schemas.py                (Pydantic)        │
│   src/core/                            (config, logging) │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Componentes do Sistema

### 3.1 API Layer — `src/api/`

Responsável por expor os endpoints REST e validar os payloads de entrada/saída via Pydantic.

| Módulo                              | Responsabilidade                                      |
|-------------------------------------|-------------------------------------------------------|
| `src/api/app.py`                    | Factory `create_app()` — configura FastAPI, CORS, middleware e routers |
| `src/api/health.py`                 | Endpoint `GET /health`                                |
| `src/api/middleware.py`             | Exception handlers centralizados (503, 504, 400, 500) |
| `src/api/dependencies.py`           | Providers de dependências FastAPI (injeção)           |
| `src/api/v1/router.py`              | Agrupa routers v1 com prefixo `/api/v1`               |
| `src/api/v1/routes/logs_routes.py`  | Handlers dos 5 endpoints de logs                      |

**Endpoints expostos:**

| Método   | Rota                | Descrição                        |
|----------|---------------------|----------------------------------|
| `POST`   | `api/v1/logs/file`  | Recebe log via upload de arquivo |
| `POST`   | `api/v1/logs/text`  | Recebe log via texto puro        |
| `GET`    | `api/v1/logs`       | Lista logs com paginação         |
| `GET`    | `api/v1/logs/{id}`  | Consulta log por ID              |
| `DELETE` | `api/v1/logs/{id}`  | Remove log por ID                |

---

### 3.2 Services Layer — `src/services/`

Contém a lógica de negócio desacoplada da camada HTTP.

| Módulo                              | Responsabilidade                                              |
|-------------------------------------|---------------------------------------------------------------|
| `src/services/log_analysis_service.py` | Orquestra pipeline: Parser → Analyzer → AIEngine → Repository. Transação atômica. |
| `src/services/log_storage_service.py`  | CRUD de leitura: `get_by_id`, `list_logs`, `delete_log`       |

---

### 3.3 Parsers Layer — `src/parsers/`

Responsável por transformar logs brutos em estruturas `LogEntry` usando **Drain3**.

| Módulo                        | Responsabilidade                                         |
|-------------------------------|----------------------------------------------------------|
| `src/parsers/base.py`         | Interface abstrata `LogParser` (ABC)                     |
| `src/parsers/drain3_parser.py`| `Drain3LogParser` — suporta JSON, Syslog RFC 3164 e texto livre |
| `src/parsers/normalizer.py`   | Normalização de severidade e inferência de timestamp     |

**Formatos suportados:**
- JSON estruturado: `{"timestamp": ..., "level": ..., "message": ...}`
- Syslog RFC 3164: `Jan 15 10:00:00 host app[pid]: message`
- Texto livre genérico (fallback)

---

### 3.4 Analyzer Layer — `src/analyzer/`

Detecta anomalias no stream de logs.

| Módulo                    | Responsabilidade                                              |
|---------------------------|---------------------------------------------------------------|
| `src/analyzer/base.py`    | Interface abstrata `LogAnalyzer` (ABC)                        |
| `src/analyzer/detector.py`| `AnomalyDetector` — spikes, stack traces, distribuição de severidade |

**Detecções implementadas:**
- Distribuição de severidade por `SeverityLevel`
- Spikes: ≥10 erros (ERROR/CRITICAL) em janela deslizante de 60s
- Stack traces: Python traceback, Java stacktrace, Go panic
- Dados insuficientes: `insufficient_data=True` se < 2 entradas

---

### 3.5 AI Layer — `src/ai/`

Integração com o modelo LLaMA 3 via Ollama, utilizando o OpenAI Python SDK como drop-in replacement.

| Módulo                    | Responsabilidade                                              |
|---------------------------|---------------------------------------------------------------|
| `src/ai/base.py`          | Interface abstrata `AIEngine` (ABC)                           |
| `src/ai/ollama_engine.py` | `OllamaAIEngine` — prompt, retry, timeout, validação Pydantic |
| `src/ai/health_check.py`  | Verificação TCP de disponibilidade do Ollama (porta 11434)    |

**Configuração do cliente:**
- Base URL: `http://localhost:11434/v1`
- Modelo: `llama3.2:3b`
- SDK: `openai` (drop-in replacement)
- Timeout: 120s por chamada
- Retry: 2 tentativas com backoff (1s, 2s)
- Amostragem: apenas entradas ERROR/CRITICAL (máx. 10)

---

### 3.6 Repository Layer — `src/repository/`

Persistência assíncrona com SQLite.

| Módulo                              | Responsabilidade                                    |
|-------------------------------------|-----------------------------------------------------|
| `src/repository/base.py`            | Interface abstrata `LogRepository` (ABC)            |
| `src/repository/sqlite_repository.py` | `SQLiteLogRepository` — CRUD com aiosqlite        |

**Schema da tabela `logs`:**

| Campo                | Tipo        | Descrição                              |
|----------------------|-------------|----------------------------------------|
| `id`                 | `TEXT PK`   | UUID do registro                       |
| `content`            | `TEXT`      | Conteúdo bruto do log                  |
| `analysis_result`    | `TEXT`      | JSON serializado do `AnalysisResult`   |
| `ai_diagnosis`       | `TEXT`      | JSON serializado do `AIDiagnosis`      |
| `issues`             | `TEXT`      | JSON serializado da lista de `Issue`   |
| `recommended_actions`| `TEXT`      | JSON serializado das ações             |
| `created_at`         | `TIMESTAMP` | Data/hora de criação                   |

---

### 3.7 Models Layer — `src/models/`

Todos os schemas Pydantic do sistema em um único módulo.

| Modelo               | Descrição                                              |
|----------------------|--------------------------------------------------------|
| `SeverityLevel`      | Enum: DEBUG, INFO, WARNING, ERROR, CRITICAL            |
| `LogEntry`           | Entrada de log normalizada                             |
| `LogTemplate`        | Template extraído pelo Drain3                          |
| `Spike`              | Pico de erros detectado em janela de tempo             |
| `AnalysisResult`     | Resultado da análise de anomalias                      |
| `Hypothesis`         | Hipótese de causa raiz gerada pela IA                  |
| `AIDiagnosis`        | Diagnóstico completo da IA (mínimo 2 hipóteses)        |
| `LogFileUpload`      | Schema de validação para upload de arquivo             |
| `LogTextUpload`      | Schema de request para envio via texto                 |
| `Issue`              | Problema agrupado por padrão (estilo Sentry)           |
| `LogAnalysisResponse`| Resposta completa da análise (estilo Datadog/Sentry)   |
| `LogListParams`      | Parâmetros de paginação                                |
| `LogListResponse`    | Response de listagem paginada                          |

---

### 3.8 Core Layer — `src/core/`

Configurações globais, dependências e utilitários transversais.

| Módulo                   | Responsabilidade                                         |
|--------------------------|----------------------------------------------------------|
| `src/core/config.py`     | `Settings` via pydantic-settings (prefixo `LOGPULSE_`)  |
| `src/core/logging.py`    | Logging estruturado                                      |
| `src/core/dependencies.py` | Providers de dependências FastAPI                      |
| `src/core/retry.py`      | Utilitário de retry com backoff exponencial              |

---

## 4. Fluxos de Dados

### 4.1 Fluxo: Envio de Log via Arquivo (`POST /api/v1/logs/file`)

```
Cliente
  │
  ├─► [1] Upload do arquivo (.log / .txt, máx 50MB)
  │
  ▼
API Layer (logs_routes.py)
  │
  ├─► [2] Validação do tipo e tamanho do arquivo (Pydantic)
  │
  ▼
LogAnalysisService.analyze_content()
  │
  ├─► [3] Drain3LogParser.parse() → list[LogEntry] + list[LogTemplate]
  │
  ├─► [4] AnomalyDetector.analyze() → AnalysisResult
  │         (spikes, stack traces, distribuição de severidade)
  │
  ├─► [5] OllamaAIEngine.diagnose() → AIDiagnosis
  │         (prompt → LLaMA 3 → hipóteses + confidence)
  │
  ├─► [6] LogAnalysisResponse.from_full_analysis()
  │         (agrupa issues, extrai recommended_actions)
  │
  ├─► [7] SQLiteLogRepository.create() → UUID
  │         (persiste analysis + diagnosis + issues + actions)
  │
  └─► [8] Retorno do JSON estruturado ao cliente (HTTP 200)
```

### 4.2 Fluxo: Envio de Log via Texto (`POST /api/v1/logs/text`)

Idêntico ao fluxo de arquivo, com a diferença de que o passo [2] recebe o texto diretamente do payload JSON, sem leitura de arquivo.

### 4.3 Fluxo: Consulta de Log (`GET /api/v1/logs/{id}`)

```
Cliente ──► API Layer ──► LogStorageService.get_by_id() ──► SQLiteLogRepository ──► JSON
```

### 4.4 Fluxo: Listagem Paginada (`GET /api/v1/logs`)

```
Cliente ──► API Layer ──► LogStorageService.list_logs() ──► SQLiteLogRepository (paginado) ──► JSON
```

### 4.5 Fluxo: Remoção de Log (`DELETE /api/v1/logs/{id}`)

```
Cliente ──► API Layer ──► LogStorageService.delete_log() ──► SQLiteLogRepository ──► 204 No Content
```

---

## 5. Integrações Externas

### 5.1 Ollama / LLaMA 3

| Atributo       | Valor                          |
|----------------|--------------------------------|
| Tipo           | LLM local                      |
| Modelo         | `llama3.2:3b`                  |
| Protocolo      | HTTP (compatível OpenAI)       |
| Endereço       | `http://localhost:11434/v1`    |
| SDK            | `openai` (drop-in replacement) |
| Pré-requisito  | Ollama instalado e em execução |
| Timeout        | 120s por chamada               |
| Retry          | 2 tentativas (backoff: 1s, 2s) |

### 5.2 Drain3

| Atributo  | Valor                                          |
|-----------|------------------------------------------------|
| Tipo      | Biblioteca Python de parsing de logs           |
| Função    | Extração de templates a partir de logs brutos  |
| Config    | depth=4, sim_th=0.4                            |

---

## 6. Decisões Técnicas (ADR Simplificado)

### ADR-001 — FastAPI como framework web

**Decisão:** Usar FastAPI.

**Justificativa:** Suporte nativo a Pydantic v2, geração automática de OpenAPI/Swagger, alta performance assíncrona e tipagem estática compatível com `mypy`.

---

### ADR-002 — SQLite como banco de dados

**Decisão:** Usar SQLite com aiosqlite.

**Justificativa:** Zero configuração, embutido no Python, suficiente para o volume de dados esperado em ambiente local/desenvolvimento. aiosqlite garante operações não bloqueantes.

---

### ADR-003 — OpenAI SDK como cliente do Ollama

**Decisão:** Usar o `openai` Python SDK apontando para `localhost:11434`.

**Justificativa:** Permite trocar o provedor de LLM (OpenAI, Gemini, Claude) no futuro apenas alterando a configuração, sem mudar o código de integração.

---

### ADR-004 — Drain3 para parsing de logs

**Decisão:** Usar Drain3 para extração de templates.

**Justificativa:** Reduz o ruído enviado ao LLM, melhora a qualidade do diagnóstico e permite agrupar logs similares com wildcards (`<*>`).

---

### ADR-005 — Resposta no estilo Datadog/Sentry

**Decisão:** `LogAnalysisResponse` com `metrics`, `issues` e `recommended_actions`.

**Justificativa:** Formato familiar para engenheiros de operações, agrupa erros por padrão (como Sentry) e apresenta métricas agregadas (como Datadog), facilitando a interpretação do diagnóstico.

---

### ADR-006 — Fallback de diagnóstico sem IA

**Decisão:** Se o Ollama falhar, retornar diagnóstico heurístico baseado em regras.

**Justificativa:** Graceful degradation — o usuário recebe uma resposta útil mesmo sem IA disponível, com `confidence` menor (0.3–0.7) para indicar menor confiabilidade.

---

## 7. Estrutura de Pastas (Referência)

```
src/
├── main.py                         # Ponto de entrada alternativo
├── exceptions.py                   # Hierarquia de exceções
├── api/
│   ├── app.py                      # Factory create_app()
│   ├── health.py                   # GET /health
│   ├── middleware.py               # Exception handlers
│   ├── dependencies.py             # Injeção de dependências (legado)
│   └── v1/
│       ├── router.py               # Agrupa routers v1
│       ├── controllers/
│       │   └── logs_controller.py  # Controller MVC: valida e delega
│       └── routes/
│           └── logs_routes.py      # View MVC: define rotas HTTP
├── services/
│   ├── log_analysis_service.py     # Pipeline: Parser→Analyzer→AI→Repo
│   └── log_storage_service.py      # CRUD de leitura e deleção
├── parsers/
│   ├── base.py                     # Interface LogParser
│   ├── drain3_parser.py            # Drain3LogParser
│   └── normalizer.py               # Normalização de severidade/timestamp
├── analyzer/
│   ├── base.py                     # Interface LogAnalyzer
│   └── detector.py                 # AnomalyDetector
├── ai/
│   ├── base.py                     # Interface AIEngine
│   ├── ollama_engine.py            # OllamaAIEngine
│   └── health_check.py             # Verificação TCP do Ollama
├── models/
│   └── schemas.py                  # Todos os schemas Pydantic
├── repository/
│   ├── base.py                     # Interface LogRepository
│   └── sqlite_repository.py        # SQLiteLogRepository
└── core/
    ├── config.py                   # Settings (pydantic-settings)
    ├── logging.py                  # Logging estruturado
    ├── dependencies.py             # Providers FastAPI
    └── retry.py                    # Retry com backoff exponencial
```

---

## 8. Considerações Futuras

- Suporte a múltiplos provedores de LLM (OpenAI, Gemini, Claude) via configuração
- Integração com fontes externas de logs (WildFly, Rancher)
- Implementação de memória semântica com embeddings
- Monitoramento de logs em tempo real (WebSocket ou SSE)
- Interface web para visualização dos diagnósticos
