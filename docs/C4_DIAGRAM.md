# Diagrama C4 — LogPulse IA

Este documento apresenta a arquitetura do LogPulse IA usando o modelo C4 (Context, Containers, Components, Code).

---

## Nível 1: Diagrama de Contexto

O diagrama de contexto mostra como o LogPulse IA se relaciona com usuários e sistemas externos.

```mermaid
C4Context
    title Diagrama de Contexto - LogPulse IA

    Person(engenheiro, "Engenheiro de Operações", "Investiga incidentes em produção")
    Person(desenvolvedor, "Desenvolvedor", "Analisa erros e stacktraces")
    
    System(logpulse, "LogPulse IA", "API REST que analisa logs e fornece diagnóstico inteligente com IA local")
    
    System_Ext(ollama, "Ollama + LLaMA 3", "Servidor LLM local na porta 11434")
    
    Rel(engenheiro, logpulse, "Envia logs via arquivo ou texto", "HTTPS/JSON")
    Rel(desenvolvedor, logpulse, "Consulta análises anteriores", "HTTPS/JSON")
    Rel(logpulse, ollama, "Solicita diagnóstico inteligente", "HTTP/OpenAI SDK")
```

**Descrição:**
- **Usuários:** Engenheiros de operações e desenvolvedores que precisam investigar incidentes rapidamente
- **LogPulse IA:** Sistema central que processa logs e gera diagnósticos
- **Ollama:** Servidor LLM local que fornece capacidades de IA sem dependências externas

---

## Nível 2: Diagrama de Containers

O diagrama de containers mostra os principais componentes técnicos do LogPulse IA.

```mermaid
C4Container
    title Diagrama de Containers - LogPulse IA

    Person(usuario, "Usuário", "Engenheiro ou Desenvolvedor")
    
    Container_Boundary(logpulse_boundary, "LogPulse IA") {
        Container(api, "API REST", "FastAPI", "Expõe endpoints para upload e consulta de logs")
        Container(parser, "Parser", "Drain3", "Transforma logs brutos em LogEntry estruturado")
        Container(analyzer, "Analyzer", "Python", "Detecta anomalias, spikes e stack traces")
        Container(ai_engine, "AI Engine", "OpenAI SDK", "Gera diagnóstico inteligente via LLM")
        ContainerDb(database, "Database", "SQLite", "Armazena logs, análises e diagnósticos")
    }
    
    System_Ext(ollama, "Ollama", "Servidor LLM local (LLaMA 3)")
    
    Rel(usuario, api, "Envia logs e consulta análises", "HTTPS/JSON")
    Rel(api, parser, "Envia log bruto", "Python")
    Rel(parser, analyzer, "Envia LogStream", "Python")
    Rel(analyzer, ai_engine, "Envia AnalysisResult", "Python")
    Rel(ai_engine, ollama, "Solicita diagnóstico", "HTTP/OpenAI SDK")
    Rel(api, database, "Persiste e consulta", "aiosqlite")
```

**Descrição dos Containers:**

| Container | Tecnologia | Responsabilidade |
|-----------|------------|------------------|
| **API REST** | FastAPI + Pydantic | Recebe requisições HTTP, valida payloads, orquestra pipeline |
| **Parser** | Drain3 | Extrai templates, normaliza severidade, infere timestamps |
| **Analyzer** | Python | Detecta spikes, agrupa stack traces, calcula distribuição |
| **AI Engine** | OpenAI SDK | Comunica com Ollama, valida respostas, implementa retry |
| **Database** | SQLite | Persistência assíncrona com aiosqlite |

---

## Nível 3: Diagrama de Componentes

O diagrama de componentes detalha a estrutura interna de cada container.

### 3.1 Container: API REST

```mermaid
C4Component
    title Componentes - API REST (FastAPI)

    Container_Boundary(api_boundary, "API REST") {
        Component(router_file, "File Router", "FastAPI Router", "POST /api/v1/logs/file")
        Component(router_text, "Text Router", "FastAPI Router", "POST /api/v1/logs/text")
        Component(router_crud, "CRUD Router", "FastAPI Router", "GET/DELETE /api/v1/logs")
        Component(service_analysis, "LogAnalysisService", "Python", "Orquestra pipeline completo")
        Component(service_storage, "LogStorageService", "Python", "Operações de consulta e deleção")
        Component(schemas, "Schemas", "Pydantic", "Validação de entrada/saída")
    }
    
    Component_Ext(parser, "Parser", "Drain3")
    Component_Ext(analyzer, "Analyzer", "Python")
    Component_Ext(ai_engine, "AI Engine", "OpenAI SDK")
    Component_Ext(repository, "Repository", "SQLite")
    
    Rel(router_file, service_analysis, "Chama analyze_content()")
    Rel(router_text, service_analysis, "Chama analyze_content()")
    Rel(router_crud, service_storage, "Chama get_by_id(), list_logs(), delete_log()")
    
    Rel(service_analysis, parser, "Usa")
    Rel(service_analysis, analyzer, "Usa")
    Rel(service_analysis, ai_engine, "Usa")
    Rel(service_analysis, repository, "Persiste resultado")
    Rel(service_storage, repository, "Consulta dados")
```

**Componentes da API:**

| Componente | Responsabilidade |
|------------|------------------|
| **File Router** | Valida arquivo (.log/.txt), tamanho (50MB), formato |
| **Text Router** | Valida texto (100k chars), aceita \n e \r\n |
| **CRUD Router** | Paginação, validação de UUID, retorno de erros HTTP |
| **LogAnalysisService** | Pipeline: Parser → Analyzer → AIEngine → Repository |
| **LogStorageService** | Consulta por ID, listagem paginada, deleção |
| **Schemas** | LogFileUpload, LogTextUpload, LogAnalysisResponse |

### 3.2 Container: Parser (Drain3)

```mermaid
C4Component
    title Componentes - Parser (Drain3)

    Container_Boundary(parser_boundary, "Parser") {
        Component(log_parser, "LogParser", "ABC", "Interface abstrata")
        Component(drain3_parser, "Drain3LogParser", "Drain3", "Implementação concreta")
        Component(normalizer, "Normalizer", "Python", "Normaliza severidade e timestamps")
        Component(format_detector, "FormatDetector", "Python", "Detecta JSON, Syslog, texto livre")
    }
    
    Component_Ext(drain3_lib, "Drain3 Library", "Biblioteca externa")
    
    Rel(drain3_parser, log_parser, "Implementa")
    Rel(drain3_parser, normalizer, "Usa")
    Rel(drain3_parser, format_detector, "Usa")
    Rel(drain3_parser, drain3_lib, "Usa para extração de templates")
```

**Componentes do Parser:**

| Componente | Responsabilidade |
|------------|------------------|
| **LogParser** | Interface abstrata com parse() e get_templates() |
| **Drain3LogParser** | Implementação com depth=4, sim_th=0.4 |
| **Normalizer** | WARN→WARNING, ERR→ERROR, FATAL→CRITICAL, TRACE→DEBUG |
| **FormatDetector** | Detecta JSON, Syslog RFC 3164, texto livre |

### 3.3 Container: Analyzer

```mermaid
C4Component
    title Componentes - Analyzer

    Container_Boundary(analyzer_boundary, "Analyzer") {
        Component(log_analyzer, "LogAnalyzer", "ABC", "Interface abstrata")
        Component(anomaly_detector, "AnomalyDetector", "Python", "Implementação concreta")
        Component(spike_detector, "SpikeDetector", "Python", "Detecta spikes de erro")
        Component(stacktrace_grouper, "StackTraceGrouper", "Python", "Agrupa stack traces")
        Component(distribution_calc, "DistributionCalculator", "Python", "Calcula distribuição de severidade")
    }
    
    Rel(anomaly_detector, log_analyzer, "Implementa")
    Rel(anomaly_detector, spike_detector, "Usa")
    Rel(anomaly_detector, stacktrace_grouper, "Usa")
    Rel(anomaly_detector, distribution_calc, "Usa")
```

**Componentes do Analyzer:**

| Componente | Responsabilidade |
|------------|------------------|
| **LogAnalyzer** | Interface abstrata com analyze() |
| **AnomalyDetector** | Orquestra detecção de anomalias |
| **SpikeDetector** | Janela deslizante de 60s, threshold de 10 erros |
| **StackTraceGrouper** | Detecta Python, Java, Go stack traces |
| **DistributionCalculator** | Contagem por SeverityLevel |

### 3.4 Container: AI Engine

```mermaid
C4Component
    title Componentes - AI Engine

    Container_Boundary(ai_boundary, "AI Engine") {
        Component(ai_engine_interface, "AIEngine", "ABC", "Interface abstrata")
        Component(ollama_engine, "OllamaAIEngine", "OpenAI SDK", "Implementação Ollama")
        Component(sampler, "Sampler", "Python", "Amostragem estratificada 70/20/10")
        Component(prompt_builder, "PromptBuilder", "Python", "Constrói prompt do sistema")
        Component(retry_handler, "RetryHandler", "Python", "Backoff exponencial 1s/2s/4s")
        Component(validator, "ResponseValidator", "Pydantic", "Valida mínimo 3 hipóteses")
    }
    
    System_Ext(ollama, "Ollama", "http://localhost:11434")
    
    Rel(ollama_engine, ai_engine_interface, "Implementa")
    Rel(ollama_engine, sampler, "Usa")
    Rel(ollama_engine, prompt_builder, "Usa")
    Rel(ollama_engine, retry_handler, "Usa")
    Rel(ollama_engine, validator, "Usa")
    Rel(ollama_engine, ollama, "Chama via OpenAI SDK")
```

**Componentes do AI Engine:**

| Componente | Responsabilidade |
|------------|------------------|
| **AIEngine** | Interface abstrata com diagnose() |
| **OllamaAIEngine** | Cliente OpenAI SDK apontando para localhost:11434 |
| **Sampler** | 70% erros, 20% warnings, 10% outros (máx 50 entradas) |
| **PromptBuilder** | Cria prompt do sistema para análise de logs |
| **RetryHandler** | 3 tentativas com backoff exponencial, timeout 30s |
| **ResponseValidator** | Valida AIDiagnosis com Pydantic |

### 3.5 Container: Database (Repository)

```mermaid
C4Component
    title Componentes - Repository (SQLite)

    Container_Boundary(repo_boundary, "Repository") {
        Component(log_repository, "LogRepository", "ABC", "Interface abstrata")
        Component(sqlite_repository, "SQLiteLogRepository", "aiosqlite", "Implementação SQLite")
        Component(transaction_manager, "TransactionManager", "Python", "Context manager para transações")
        Component(serializer, "Serializer", "JSON", "Serializa/desserializa Pydantic")
    }
    
    ContainerDb(sqlite, "SQLite Database", "logs.db")
    
    Rel(sqlite_repository, log_repository, "Implementa")
    Rel(sqlite_repository, transaction_manager, "Usa")
    Rel(sqlite_repository, serializer, "Usa")
    Rel(sqlite_repository, sqlite, "Operações CRUD assíncronas")
```

**Componentes do Repository:**

| Componente | Responsabilidade |
|------------|------------------|
| **LogRepository** | Interface com create(), get_by_id(), list_paginated(), delete() |
| **SQLiteLogRepository** | Implementação assíncrona com aiosqlite |
| **TransactionManager** | Rollback automático em caso de falha |
| **Serializer** | JSON para AnalysisResult e AIDiagnosis |

---

## Nível 4: Diagrama de Código (Modelos de Dados)

O diagrama de código mostra as principais classes e suas relações.

```mermaid
classDiagram
    class SeverityLevel {
        <<enumeration>>
        DEBUG
        INFO
        WARNING
        ERROR
        CRITICAL
    }
    
    class LogEntry {
        +datetime timestamp
        +SeverityLevel level
        +str message
        +str raw_line
        +int template_id
        +bool timestamp_inferred
        +bool level_inferred
    }
    
    class LogTemplate {
        +int id
        +str pattern
        +int occurrences
        +list~str~ sample_messages
    }
    
    class Spike {
        +datetime start_time
        +datetime end_time
        +int error_count
        +SeverityLevel severity
    }
    
    class AnalysisResult {
        +int total_entries
        +int error_count
        +int warning_count
        +bool insufficient_data
        +list~Spike~ spikes
        +list~LogTemplate~ templates
        +dict~SeverityLevel,int~ severity_distribution
    }
    
    class Hypothesis {
        +str description
        +str probability
        +str action
        +int related_line
    }
    
    class AIDiagnosis {
        +str summary
        +str probable_cause
        +list~Hypothesis~ hypotheses
    }
    
    class LogAnalysisResponse {
        +str id
        +datetime created_at
        +int total_entries
        +int error_count
        +int warning_count
        +bool insufficient_data
        +list~str~ spikes
        +list~str~ anomalies
        +AIDiagnosis ai_diagnosis
    }
    
    LogEntry --> SeverityLevel
    LogEntry --> LogTemplate
    Spike --> SeverityLevel
    AnalysisResult --> Spike
    AnalysisResult --> LogTemplate
    AnalysisResult --> SeverityLevel
    AIDiagnosis --> Hypothesis
    LogAnalysisResponse --> AIDiagnosis
```

**Relacionamentos:**
- `LogEntry` usa `SeverityLevel` e referencia `LogTemplate` via `template_id`
- `AnalysisResult` agrega `Spike`, `LogTemplate` e distribuição de `SeverityLevel`
- `AIDiagnosis` contém lista de `Hypothesis` (mínimo 3)
- `LogAnalysisResponse` é o schema de saída da API, contendo `AIDiagnosis`

---

## Pipeline de Dados (Fluxo End-to-End)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant API as API REST
    participant P as Parser
    participant A as Analyzer
    participant AI as AI Engine
    participant O as Ollama
    participant DB as SQLite

    U->>API: POST /api/v1/logs/file (arquivo.log)
    API->>API: Valida formato e tamanho
    API->>P: parse(raw_content)
    P->>P: Detecta formato (JSON/Syslog/texto)
    P->>P: Normaliza severidade
    P->>P: Extrai templates com Drain3
    P-->>API: list[LogEntry] + list[LogTemplate]
    
    API->>A: analyze(entries, templates)
    A->>A: Calcula distribuição
    A->>A: Detecta spikes (janela 60s)
    A->>A: Agrupa stack traces
    A-->>API: AnalysisResult
    
    API->>AI: diagnose(analysis_result, sample_entries)
    AI->>AI: Amostragem estratificada (70/20/10)
    AI->>AI: Constrói prompt
    AI->>O: POST /v1/chat/completions (llama3)
    O-->>AI: Resposta JSON
    AI->>AI: Valida resposta (min 3 hipóteses)
    AI-->>API: AIDiagnosis
    
    API->>DB: create(content, analysis, diagnosis)
    DB-->>API: UUID gerado
    API-->>U: HTTP 200 + LogAnalysisResponse
```

**Etapas do Pipeline:**
1. **Validação:** API valida formato, tamanho e campos obrigatórios
2. **Parsing:** Drain3 extrai templates e normaliza dados
3. **Análise:** Detector identifica anomalias e calcula métricas
4. **Diagnóstico:** Ollama gera hipóteses de causa raiz via LLM
5. **Persistência:** SQLite armazena log, análise e diagnóstico
6. **Resposta:** API retorna JSON estruturado com UUID

---

## Decisões Arquiteturais

### 1. Arquitetura em Camadas com Inversão de Dependências

**Decisão:** Usar arquitetura em camadas (API → Services → Domain → Infrastructure) com interfaces abstratas (ABC).

**Justificativa:**
- Facilita testes unitários com mocks
- Permite trocar implementações (ex: SQLite → PostgreSQL)
- Separa lógica de negócio de detalhes técnicos

### 2. Drain3 para Extração de Templates

**Decisão:** Usar biblioteca Drain3 em vez de regex manual.

**Justificativa:**
- Algoritmo comprovado para log parsing
- Agrupa mensagens similares automaticamente
- Reduz complexidade de manutenção

### 3. Ollama Local via OpenAI SDK

**Decisão:** Usar Ollama local com OpenAI SDK como drop-in replacement.

**Justificativa:**
- Sem custos de API externa
- Privacidade dos dados (logs não saem do ambiente)
- Compatibilidade com OpenAI SDK facilita migração futura

### 4. SQLite para Persistência

**Decisão:** Usar SQLite em vez de PostgreSQL/MySQL.

**Justificativa:**
- MVP não requer alta concorrência
- Zero configuração (serverless)
- Suficiente para análises históricas

### 5. FastAPI + Pydantic

**Decisão:** Usar FastAPI com validação Pydantic.

**Justificativa:**
- Validação automática de schemas
- Documentação interativa (Swagger)
- Performance superior (async/await)

---

## Requisitos Não Funcionais Mapeados

| Requisito | Componente Responsável | Implementação |
|-----------|------------------------|---------------|
| **RNF-01** (Performance 50MB) | Parser | Leitura linha a linha, sem carregar arquivo inteiro |
| **RNF-02** (Parsing < 1ms) | Drain3LogParser | Algoritmo otimizado do Drain3 |
| **RNF-03** (Resiliência) | Parser | Try-catch por linha, continua processamento |
| **RNF-04** (Segurança) | AI Engine | Envia apenas AnalysisResult + amostras, não log completo |
| **RNF-05** (Qualidade) | Todos | mypy --strict, black, isort, ruff |
| **RNF-06** (Testes 30%) | Todos | pytest + hypothesis |
| **RNF-07** (Python 3.11+) | Todos | Type hints, tomllib stdlib |
| **RNF-08** (Timeout 30s) | AI Engine | RetryHandler com timeout e backoff |
| **RNF-09** (Qualidade IA) | AI Engine | Validação de resposta com Pydantic |

---

## Roadmap de Evolução Arquitetural

### Versão 2 (Fora do MVP)

```mermaid
graph LR
    A[LogPulse IA v2] --> B[Múltiplos LLMs]
    A --> C[Integração WildFly]
    A --> D[Integração Rancher]
    A --> E[Memória com Embeddings]
    A --> F[Monitoramento Real-time]
    
    B --> B1[OpenAI]
    B --> B2[Gemini]
    B --> B3[Claude]
    
    E --> E1[Vector Database]
    E --> E2[Semantic Search]
```

**Mudanças Arquiteturais Previstas:**
- **Múltiplos LLMs:** Factory pattern para trocar provider
- **Integrações:** Adapters para WildFly, Rancher, Kubernetes
- **Embeddings:** Vector database (Qdrant/Weaviate) para memória semântica
- **Real-time:** WebSocket para streaming de logs
- **Interface Web:** Frontend React/Vue para visualização

---

## Conclusão

O LogPulse IA segue uma arquitetura modular e extensível, com separação clara de responsabilidades:

- **API REST:** Ponto de entrada com validação rigorosa
- **Parser:** Transformação de logs brutos em dados estruturados
- **Analyzer:** Detecção inteligente de anomalias
- **AI Engine:** Diagnóstico com IA local via Ollama
- **Repository:** Persistência assíncrona com SQLite

A arquitetura suporta os requisitos do MVP e permite evolução futura sem grandes refatorações.
