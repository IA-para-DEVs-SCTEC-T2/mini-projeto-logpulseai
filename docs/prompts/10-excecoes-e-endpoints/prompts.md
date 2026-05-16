# Prompts — Etapa 10: Exceções e Endpoints API

Prompts utilizados durante a implementação das tarefas de exceções customizadas e endpoints da API REST.

---

## P10-01 — Criar Hierarquia de Exceções Customizadas

**Data:** 2025-05-15
**Ferramenta:** Kiro
**Issue:** #289

**Prompt:**
```
implemente a tarefa, crie a branch e commite conforme estabelecido em .github, documente os prompts utilizados para a construção da tarefa em docs/prompts. No final pode dar o push

Criar hierarquia de exceções customizadas
Tarefa Principal: #289
Descrição: Criar hierarquia de exceções para o sistema
Critérios de Aceitação
Estimativa: 1h
```

**Resultado:**
Hierarquia de exceções customizadas expandida e validada com testes:

✅ **Arquivo: `src/exceptions.py`** (ATUALIZADO)
- `LogPulseError` — exceção base do sistema
- `ConfigError` — erro de configuração (logpulse.toml inválido)
- `ValidationError` — erro de validação de dados de entrada
- `NotFoundError` — recurso não encontrado
- `AIEngineError` — erro base de comunicação com IA
  - `AIEngineTimeoutError` — timeout após tentativas
  - `AIEngineUnavailableError` — serviço indisponível
- `ParsingError` — erro ao parsear conteúdo de log
- `AnalysisError` — erro durante análise de anomalias
- `StorageError` — erro de persistência SQLite

✅ **Arquivo: `tests/test_exceptions.py`** (NOVO)
- 23 testes cobrindo hierarquia, instanciação e comportamento de captura
- Validação de herança entre todas as exceções
- Validação de mensagens descritivas
- Validação de catch behavior hierárquico

**Métricas:**
- Testes: 23 passed ✅
- Branch: `feature/hierarquia-excecoes-customizadas`
- Commit: `feat: cria hierarquia de excecoes customizadas do sistema`

---

## P10-02 — Criar Router para GET /api/v1/logs/{id}

**Data:** 2025-05-15
**Ferramenta:** Kiro
**Issue:** #284

**Prompt:**
```
Criar router para GET /api/v1/logs/{id}
Tarefa Principal: #284
Descrição: Endpoint para consulta de log por ID
Critérios de Aceitação
Estimativa: 1h
Requisitos: RF-06.2, RF-06.3
```

**Resultado:**
Endpoint GET /api/v1/logs/{id} implementado com testes:

✅ **Arquivos criados:**
- `src/api/__init__.py` — módulo API
- `src/api/v1/__init__.py` — módulo API v1
- `src/api/dependencies.py` — injeção de dependências (repositório)
- `src/api/v1/logs.py` — router GET /api/v1/logs/{id}
- `tests/api/__init__.py` — módulo de testes API
- `tests/api/v1/__init__.py` — módulo de testes API v1
- `tests/api/v1/test_get_log_by_id.py` — 6 testes

✅ **Funcionalidades:**
- Retorna 200 com dados completos quando log existe
- Retorna 404 quando log não encontrado
- Resposta contém analysis, diagnosis e created_at
- Repositório chamado com ID correto

**Métricas:**
- Testes: 6 passed ✅
- Branch: `feature/router-get-logs-by-id`
- Commit: `feat(api): cria router para GET /api/v1/logs/{id}`

---

## P10-03 — Criar Router para POST /api/v1/logs/file

**Data:** 2025-05-15
**Ferramenta:** Kiro
**Issue:** #284

**Prompt:**
```
Criar router para POST /api/v1/logs/file
Tarefa Principal: #284
Descrição: Endpoint para upload de arquivo de log
Critérios de Aceitação
Estimativa: 2h
Requisitos: RF-01.1, RF-01.2, RF-01.3, RF-01.4
```

**Resultado:**
Endpoint POST /api/v1/logs/file implementado com pipeline completo:

✅ **Arquivos criados:**
- `src/api/v1/logs_file.py` — router POST /api/v1/logs/file
- `tests/api/v1/test_post_logs_file.py` — 7 testes

✅ **Pipeline implementado:**
1. Validação de extensão (.log, .txt)
2. Validação de tamanho (máx. 50MB)
3. Validação de conteúdo não vazio
4. Parse via Drain3LogParser
5. Análise via AnomalyDetector
6. Diagnóstico via OllamaAIEngine
7. Persistência via SQLiteLogRepository

✅ **Validações:**
- 400 para extensão inválida
- 400 para arquivo vazio
- 400 para arquivo com apenas espaços
- 503 quando IA indisponível
- 201 com resposta completa para arquivo válido

**Métricas:**
- Testes: 7 passed ✅
- Branch: `feature/router-post-logs-file`
- Commit: `feat(api): cria router para POST /api/v1/logs/file`

---

## P10-04 — Criar Router para GET /api/v1/logs

**Data:** 2025-05-15
**Ferramenta:** Kiro
**Issue:** #284

**Prompt:**
```
Criar router para GET /api/v1/logs
Tarefa Principal: #284
Descrição: Endpoint para listagem paginada de logs
Critérios de Aceitação
Estimativa: 1h
Requisitos: RF-06.4
```

**Resultado:**
Endpoint GET /api/v1/logs implementado com paginação:

✅ **Arquivos criados/modificados:**
- `src/api/v1/logs_list.py` — router GET /api/v1/logs
- `src/repository/base.py` — adicionado método abstrato `count()`
- `src/repository/sqlite_repository.py` — implementação de `count()`
- `tests/api/v1/test_get_logs_list.py` — 8 testes

✅ **Funcionalidades:**
- Paginação com page e page_size (query params)
- page_size máximo de 100
- Cálculo de total de páginas (arredonda para cima)
- Ordenação por data de criação (mais recente primeiro)
- Resposta com items, total, page, page_size, pages

**Métricas:**
- Testes: 8 passed ✅
- Branch: `feature/router-get-logs-listagem`
- Commit: `feat(api): cria router para GET /api/v1/logs com paginacao`

---

## P10-05 — Criar Router para POST /api/v1/logs/text

**Data:** 2025-05-15
**Ferramenta:** Kiro
**Issue:** #284

**Prompt:**
```
Criar router para POST /api/v1/logs/text
Tarefa Principal: #284
Descrição: Endpoint para envio de log via texto
Critérios de Aceitação
Estimativa: 1h
Requisitos: RF-02.1, RF-02.2, RF-02.3, RF-02.4
```

**Resultado:**
Endpoint POST /api/v1/logs/text implementado com pipeline completo:

✅ **Arquivos criados:**
- `src/api/v1/logs_text.py` — router POST /api/v1/logs/text
- `tests/api/v1/test_post_logs_text.py` — 8 testes

✅ **Pipeline implementado:**
1. Validação via Pydantic (LogTextUpload: min_length=1, max_length=100000)
2. Validação de conteúdo não apenas espaços
3. Parse via Drain3LogParser
4. Análise via AnomalyDetector
5. Diagnóstico via OllamaAIEngine
6. Persistência via SQLiteLogRepository

✅ **Validações:**
- 422 para conteúdo vazio (Pydantic)
- 422 para campo content ausente
- 400 para conteúdo com apenas espaços
- 503 quando IA indisponível
- 503 quando IA timeout
- 201 com resposta completa para texto válido

**Métricas:**
- Testes: 8 passed ✅
- Branch: `feature/router-post-logs-text`
- Commit: `feat(api): cria router para POST /api/v1/logs/text`

---

## Resumo de Branches e Commits

| Branch | Commit | Issue |
|--------|--------|-------|
| `feature/hierarquia-excecoes-customizadas` | `feat: cria hierarquia de excecoes customizadas do sistema` | #289 |
| `feature/router-get-logs-by-id` | `feat(api): cria router para GET /api/v1/logs/{id}` | #284 |
| `feature/router-post-logs-file` | `feat(api): cria router para POST /api/v1/logs/file` | #284 |
| `feature/router-get-logs-listagem` | `feat(api): cria router para GET /api/v1/logs com paginacao` | #284 |
| `feature/router-post-logs-text` | `feat(api): cria router para POST /api/v1/logs/text` | #284 |

## Total de Testes Criados: 52

- test_exceptions.py: 23 testes
- test_get_log_by_id.py: 6 testes
- test_post_logs_file.py: 7 testes
- test_get_logs_list.py: 8 testes
- test_post_logs_text.py: 8 testes
