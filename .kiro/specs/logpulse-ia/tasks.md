# Plano de Implementação: LogPulse IA

## Visão Geral

Este documento contém as tarefas de implementação para o LogPulse IA, uma API REST construída com FastAPI que analisa logs brutos e fornece diagnóstico inteligente com IA local (Ollama + LLaMA 3). A implementação segue uma abordagem incremental, com validação contínua através de testes.

## Tarefas

- [x] 1. Configurar estrutura do projeto e dependências
  - **Descrição:** Criar estrutura inicial do projeto Python com todas as dependências e ferramentas de qualidade configuradas
  - **Critérios de Aceitação:**
    - ✅ Estrutura de pastas criada: `src/`, `tests/`, `logs/`, `docs/`
    - ✅ `pyproject.toml` configurado com: FastAPI, Pydantic, Drain3, OpenAI SDK, aiosqlite, pytest, hypothesis
    - ✅ Ferramentas de qualidade configuradas: mypy (strict), black, isort, ruff
    - ✅ Arquivo `.env.example` criado com variáveis de ambiente
    - ✅ Comando `pip install -e .` executa sem erros
  - **Dependências:** Nenhuma
  - **Estimativa:** 1-2 horas
  - _Requisitos: RNF-05, RNF-07_

- [x] 2. Implementar modelos de dados com Pydantic
  - **Descrição:** Criar todos os modelos Pydantic que representam dados do sistema (logs, análises, diagnósticos)
  - **Critérios de Aceitação:**
    - ✅ Enum `SeverityLevel` com valores: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - ✅ Modelo `LogEntry` com campos obrigatórios e flags de inferência
    - ✅ Modelo `LogTemplate` com pattern, occurrences, sample_messages (máx 5)
    - ✅ Modelo `Spike` com start_time, end_time, error_count, template_ids
    - ✅ Modelo `AnalysisResult` com contadores, distribuição, spikes, stack_traces
    - ✅ Modelo `Hypothesis` com description, probability, action, related_line
    - ✅ Modelo `AIDiagnosis` com summary, probable_cause, hypotheses (mín 2), suggested_fix, confidence
    - ✅ Schemas de API: LogFileUpload, LogTextUpload, LogAnalysisResponse (estilo Datadog/Sentry), LogListParams, LogListResponse
    - ✅ Modelo `Issue` para agrupamento de erros por padrão
  - **Dependências:** Tarefa 1
  - **Estimativa:** 3-4 horas
  - _Requisitos: RF-03.1, RF-03.4, RF-04.2, RF-04.4, RF-05.2, RF-05.3, RF-01.1, RF-02.2, RF-07.1_
  - [x] 2.1 Criar modelos base (SeverityLevel, LogEntry, LogTemplate)
    - ✅ Implementado em `src/models/schemas.py`
    - _Requisitos: RF-03.1, RF-03.4_
  
  - [x] 2.2 Criar modelos de análise (Spike, AnalysisResult)
    - ✅ Implementado em `src/models/schemas.py`
    - _Requisitos: RF-04.2, RF-04.4_
  
  - [x] 2.3 Criar modelos de diagnóstico IA (Hypothesis, AIDiagnosis)
    - ✅ Implementado em `src/models/schemas.py`
    - ✅ Mínimo de 2 hipóteses (ajustado da spec original de 3)
    - _Requisitos: RF-05.2, RF-05.3_
  
  - [x] 2.4 Criar schemas de request/response da API
    - ✅ Implementado em `src/models/schemas.py`
    - ✅ `LogAnalysisResponse` no estilo Datadog/Sentry com `metrics`, `issues`, `recommended_actions`, `confidence`
    - _Requisitos: RF-01.1, RF-02.2, RF-07.1_

- [x] 3. Implementar Parser de Logs com Drain3
  - **Descrição:** Criar componente que transforma logs brutos em estruturas LogEntry usando Drain3 para extração de templates
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `LogParser` com métodos `parse()` e `get_templates()` em `src/parsers/base.py`
    - ✅ `Drain3LogParser` configurado com depth=4 e sim_th=0.4 em `src/parsers/drain3_parser.py`
    - ✅ Reconhece 3 formatos: JSON estruturado, Syslog RFC 3164, texto livre
    - ✅ Normaliza aliases: WARN→WARNING, ERR→ERROR, FATAL→CRITICAL, TRACE→DEBUG em `src/parsers/normalizer.py`
    - ✅ Infere timestamp quando ausente (flag `timestamp_inferred=True`)
    - ✅ Infere level quando ausente (default INFO, flag `level_inferred=True`)
    - ✅ Extrai templates com Drain3 e atribui template_id
    - ✅ Coleta até 5 sample_messages por template
    - ✅ Linhas malformadas são ignoradas sem interromper o processamento
  - **Dependências:** Tarefa 2
  - **Estimativa:** 6-8 horas
  - _Requisitos: RF-03.1, RF-03.2, RF-03.3, RF-03.4, RF-03.5, RF-03.6, RNF-02, RNF-03_
  - [x] 3.1 Criar interface abstrata LogParser
    - ✅ Implementado em `src/parsers/base.py`
    - _Requisitos: RF-03.1_
  
  - [x] 3.2 Implementar Drain3LogParser
    - ✅ Implementado em `src/parsers/drain3_parser.py`
    - _Requisitos: RF-03.2, RF-03.3_
  
  - [x] 3.3 Implementar normalização de severidade
    - ✅ Implementado em `src/parsers/normalizer.py` — função `normalize_severity()`
    - _Requisitos: RF-03.4, RF-03.6_
  
  - [x] 3.4 Implementar inferência de timestamp
    - ✅ Implementado em `src/parsers/normalizer.py` — funções `parse_timestamp()` e `extract_timestamp_from_line()`
    - _Requisitos: RF-03.5_
  
  - [x] 3.5 Implementar extração de templates
    - ✅ Implementado em `src/parsers/drain3_parser.py` — método `_process_template()`
    - _Requisitos: RF-03.1_

- [x] 4. Checkpoint - Validar Parser
  - ✅ Parser implementado e testado em `tests/parsers/`
  - _Requisitos: RF-03.*, RNF-03_

- [x] 5. Implementar Analyzer de Anomalias
  - **Descrição:** Criar componente que detecta anomalias (spikes, stack traces) em um LogStream
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `LogAnalyzer` com método `analyze()` em `src/analyzer/base.py`
    - ✅ `AnomalyDetector` implementado em `src/analyzer/detector.py`
    - ✅ Calcula distribuição de severidade (contagem por SeverityLevel)
    - ✅ Detecta spikes: ≥10 erros (ERROR/CRITICAL) em janela deslizante de 60s
    - ✅ Detecta e agrupa Python traceback, Java stacktrace, Go panic
    - ✅ Retorna `insufficient_data=True` se < 2 entradas
  - **Dependências:** Tarefa 2, Tarefa 4
  - **Estimativa:** 5-6 horas
  - _Requisitos: RF-04.1, RF-04.2, RF-04.3, RF-04.4, RF-04.5, RN-01, RN-02_
  - [x] 5.1 Criar interface abstrata LogAnalyzer
    - ✅ Implementado em `src/analyzer/base.py`
    - _Requisitos: RF-04.1_
  
  - [x] 5.2 Implementar AnomalyDetector
    - ✅ Implementado em `src/analyzer/detector.py`
    - _Requisitos: RF-04.1, RF-04.4, RF-04.5_
  
  - [x] 5.3 Implementar detecção de spikes
    - ✅ Implementado em `src/analyzer/detector.py` — método `_detect_spikes()`
    - _Requisitos: RF-04.2, RN-02_
  
  - [x] 5.4 Implementar agrupamento de stack traces
    - ✅ Implementado em `src/analyzer/detector.py` — método `_detect_stack_traces()`
    - _Requisitos: RF-04.3_

- [x] 6. Implementar AIEngine com Ollama
  - **Descrição:** Criar componente que usa Ollama/LLaMA 3 para gerar diagnóstico inteligente a partir da análise
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `AIEngine` com método `diagnose()` em `src/ai/base.py`
    - ✅ `OllamaAIEngine` implementado em `src/ai/ollama_engine.py`
    - ✅ Amostragem: filtra apenas ERROR/CRITICAL (máx 10 entradas) para otimizar performance
    - ✅ Prompt do sistema para análise de logs criado
    - ✅ Chamada ao Ollama com modelo llama3 via OpenAI SDK
    - ✅ Timeout de 60s por chamada
    - ✅ Retry com backoff exponencial: 2 tentativas (1s, 2s)
    - ✅ Verifica disponibilidade do Ollama via TCP em `src/ai/health_check.py`
    - ✅ Valida resposta com schema Pydantic AIDiagnosis
    - ✅ Lança `AIEngineTimeoutError` após tentativas esgotadas
    - ✅ Lança `AIEngineUnavailableError` se Ollama indisponível
    - ✅ Fallback heurístico em `LogAnalysisService` se IA falhar
    - ✅ Ajuste de confidence baseado nas evidências concretas
  - **Dependências:** Tarefa 2, Tarefa 5
  - **Estimativa:** 6-8 horas
  - _Requisitos: RF-05.1, RF-05.2, RF-05.3, RF-05.5, RF-05.7, RNF-04, RNF-08_
  - [x] 6.1 Criar interface abstrata AIEngine
    - ✅ Implementado em `src/ai/base.py`
    - _Requisitos: RF-05.1_
  
  - [x] 6.2 Implementar OllamaAIEngine
    - ✅ Implementado em `src/ai/ollama_engine.py`
    - _Requisitos: RF-05.1, RNF-04_
  
  - [x] 6.3 Implementar timeout e retry com backoff exponencial
    - ✅ Implementado em `src/ai/ollama_engine.py` — 2 tentativas com delays [1s, 2s]
    - _Requisitos: RF-05.7, RNF-08_
  
  - [x] 6.4 Implementar validação de disponibilidade do Ollama
    - ✅ Implementado em `src/ai/health_check.py` — verificação TCP na porta 11434
    - _Requisitos: RF-05.5_
  
  - [x] 6.5 Implementar validação de resposta do LLM
    - ✅ Implementado em `src/ai/ollama_engine.py` — função `_parse_llm_response()` com Pydantic
    - _Requisitos: RF-05.2, RF-05.3_

- [x] 7. Checkpoint - Validar componentes core
  - ✅ Parser, Analyzer e AIEngine implementados e com testes em `tests/`
  - _Requisitos: RF-03.*, RF-04.*, RF-05.*_

- [x] 8. Implementar camada de persistência (Repository)
  - **Descrição:** Criar camada de persistência com SQLite para armazenar logs analisados
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `LogRepository` com métodos CRUD em `src/repository/base.py`
    - ✅ `SQLiteLogRepository` implementado em `src/repository/sqlite_repository.py`
    - ✅ Schema: logs(id, content, analysis_result, ai_diagnosis, issues, recommended_actions, created_at)
    - ✅ Índice em created_at para paginação eficiente
    - ✅ Operações CRUD assíncronas com aiosqlite
    - ✅ Serialização de AnalysisResult e AIDiagnosis como JSON
    - ✅ Migração automática para adicionar colunas issues e recommended_actions
  - **Dependências:** Tarefa 2, Tarefa 7
  - **Estimativa:** 4-5 horas
  - _Requisitos: RF-06.1, RF-06.2, RF-06.3, RF-06.4, RF-06.5, RF-06.6, RNF-01_
  - [x] 8.1 Criar interface abstrata LogRepository
    - ✅ Implementado em `src/repository/base.py`
    - _Requisitos: RF-06.1, RF-06.2, RF-06.4, RF-06.5_
  
  - [x] 8.2 Implementar SQLiteLogRepository
    - ✅ Implementado em `src/repository/sqlite_repository.py`
    - _Requisitos: RF-06.1, RNF-01_
  
  - [x] 8.3 Implementar transações atômicas
    - ✅ Implementado via `async with aiosqlite.connect()` com commit/rollback automático
    - _Requisitos: RF-06.1_

- [x] 9. Implementar camada de serviço (Services)
  - **Descrição:** Criar camada de serviço que orquestra o pipeline completo de análise
  - **Critérios de Aceitação:**
    - ✅ `LogAnalysisService.analyze_content()` orquestra: Parser → Analyzer → AIEngine → Repository em `src/services/log_analysis_service.py`
    - ✅ Fallback heurístico quando IA indisponível (graceful degradation)
    - ✅ Transação atômica: só persiste se análise completa for bem-sucedida
    - ✅ `LogStorageService` implementado em `src/services/log_storage_service.py`
    - ✅ `get_by_id()`, `list_logs()`, `delete_log()` implementados
  - **Dependências:** Tarefas 3, 5, 6, 8
  - **Estimativa:** 3-4 horas
  - _Requisitos: RF-01.5, RF-02.5, RF-06.1, RF-06.2, RF-06.4, RF-06.5_
  - [x] 9.1 Implementar LogAnalysisService
    - ✅ Implementado em `src/services/log_analysis_service.py`
    - _Requisitos: RF-01.5, RF-02.5, RF-06.1_
  
  - [x] 9.2 Implementar LogStorageService
    - ✅ Implementado em `src/services/log_storage_service.py`
    - _Requisitos: RF-06.2, RF-06.4, RF-06.5_

- [x] 10. Implementar endpoints da API (Routers)
  - **Descrição:** Criar todos os endpoints REST da API com FastAPI
  - **Critérios de Aceitação:**
    - ✅ POST /api/v1/logs/file: aceita .log/.txt, max 50MB
    - ✅ POST /api/v1/logs/text: aceita content, max 100k chars
    - ✅ GET /api/v1/logs: paginação (page≥1, page_size≤100)
    - ✅ GET /api/v1/logs/{id}: retorna log completo ou HTTP 404
    - ✅ DELETE /api/v1/logs/{id}: remove log, retorna HTTP 204/404
    - ✅ Middleware de exception handlers em `src/api/middleware.py`
    - ✅ Factory `create_app()` em `src/api/app.py`
    - ✅ Health check em `GET /health`
    - ✅ Swagger UI em `/docs` e ReDoc em `/redoc`
  - **Dependências:** Tarefas 2, 9
  - **Estimativa:** 5-6 horas
  - _Requisitos: RF-01.*, RF-02.*, RF-06.*, RF-07.5_
  - [x] 10.1 Criar router para POST /api/v1/logs/file
    - ✅ Implementado em `src/api/v1/routes/logs_routes.py`
    - _Requisitos: RF-01.1, RF-01.2, RF-01.3, RF-01.4_
  
  - [x] 10.2 Criar router para POST /api/v1/logs/text
    - ✅ Implementado em `src/api/v1/routes/logs_routes.py`
    - _Requisitos: RF-02.1, RF-02.2, RF-02.3, RF-02.4_
  
  - [x] 10.3 Criar router para GET /api/v1/logs
    - ✅ Implementado em `src/api/v1/routes/logs_routes.py`
    - _Requisitos: RF-06.4_
  
  - [x] 10.4 Criar router para GET /api/v1/logs/{id}
    - ✅ Implementado em `src/api/v1/routes/logs_routes.py`
    - _Requisitos: RF-06.2, RF-06.3_
  
  - [x] 10.5 Criar router para DELETE /api/v1/logs/{id}
    - ✅ Implementado em `src/api/v1/routes/logs_routes.py`
    - _Requisitos: RF-06.5, RF-06.6_

- [ ] 11. Validar cobertura de testes (≥ 30%)
  - **Descrição:** Garantir que a cobertura mínima de 30% está sendo atingida
  - **Critérios de Aceitação:**
    - [ ] `pytest --cov=src --cov-fail-under=30` passa sem erros
    - [ ] Módulos críticos (parsers, analyzer, ai, repository) têm cobertura adequada
    - [ ] Testes de property-based testing com hypothesis estão presentes
  - **Dependências:** Todas as tarefas anteriores
  - **Estimativa:** 2-3 horas
  - _Requisitos: RNF-06_
