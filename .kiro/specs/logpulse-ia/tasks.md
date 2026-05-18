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
    - ✅ Arquivo `.env.example` criado com variáveis: OLLAMA_URL, DATABASE_PATH, LOG_LEVEL
    - ✅ Comando `pip install -e .` executa sem erros
  - **Definition of Done:**
    - [ ] Todas as pastas existem e estão vazias (exceto `.gitkeep`)
    - [ ] `pyproject.toml` tem todas as dependências listadas
    - [ ] `mypy --strict src/` executa sem erros (mesmo com src/ vazio)
    - [ ] `.env.example` tem todas as variáveis documentadas
  - **Dependências:** Nenhuma
  - **Estimativa:** 1-2 horas
  - _Requisitos: RNF-05, RNF-07_

- [ ] 2. Implementar modelos de dados com Pydantic
  - **Descrição:** Criar todos os modelos Pydantic que representam dados do sistema (logs, análises, diagnósticos)
  - **Critérios de Aceitação:**
    - ✅ Enum `SeverityLevel` com valores: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - ✅ Modelo `LogEntry` com campos obrigatórios e flags de inferência
    - ✅ Modelo `LogTemplate` com pattern, occurrences, sample_messages
    - ✅ Modelo `Spike` com start_time, end_time, error_count
    - ✅ Modelo `AnalysisResult` com contadores e distribuição
    - ✅ Modelo `Hypothesis` com description, probability, action
    - ✅ Modelo `AIDiagnosis` com summary, probable_cause, hypotheses (min 3)
    - ✅ Schemas de API: LogFileUpload, LogTextUpload, LogAnalysisResponse, LogListParams
  - **Definition of Done:**
    - [ ] Todos os modelos passam em `mypy --strict`
    - [ ] Validação Pydantic funciona (ex: LogTextUpload rejeita content > 100k chars)
    - [ ] Testes unitários cobrem validações de cada modelo
  - **Dependências:** Tarefa 1 (estrutura do projeto)
  - **Estimativa:** 3-4 horas
  - _Requisitos: RF-03.1, RF-03.4, RF-04.2, RF-04.4, RF-05.2, RF-05.3, RF-01.1, RF-02.2, RF-07.1_
  - [ ] 2.1 Criar modelos base (SeverityLevel, LogEntry, LogTemplate)
    - **Descrição:** Criar modelos Pydantic fundamentais para representar logs e templates
    - **Critérios de Aceitação:**
      - ✅ Enum `SeverityLevel` com valores: DEBUG, INFO, WARNING, ERROR, CRITICAL
      - ✅ Modelo `LogEntry` com campos: timestamp, level, message, raw_line, template_id
      - ✅ Flags de inferência: `timestamp_inferred`, `level_inferred` (bool)
      - ✅ Modelo `LogTemplate` com: pattern (str), occurrences (int), sample_messages (list[str], max 5)
    - **Definition of Done:**
      - [ ] Enum SeverityLevel aceita apenas valores válidos
      - [ ] LogEntry valida tipos de todos os campos
      - [ ] LogTemplate limita sample_messages a 5 itens
    - **Estimativa:** 1h
    - _Requisitos: RF-03.1, RF-03.4_
  
  - [ ] 2.2 Criar modelos de análise (Spike, AnalysisResult)
    - **Descrição:** Criar modelos para representar resultados da análise de anomalias
    - **Critérios de Aceitação:**
      - ✅ Modelo `Spike` com: start_time (datetime), end_time (datetime), error_count (int), severity (SeverityLevel)
      - ✅ Modelo `AnalysisResult` com: total_entries, error_count, warning_count, spikes (list[Spike])
      - ✅ Campo `templates` (list[LogTemplate]) em AnalysisResult
      - ✅ Campo `severity_distribution` (dict[SeverityLevel, int]) em AnalysisResult
      - ✅ Campo `insufficient_data` (bool) em AnalysisResult
    - **Definition of Done:**
      - [ ] Spike valida que end_time > start_time
      - [ ] AnalysisResult valida que contadores são não-negativos
      - [ ] severity_distribution soma igual a total_entries
    - **Estimativa:** 1h
    - _Requisitos: RF-04.2, RF-04.4_
  
  - [ ] 2.3 Criar modelos de diagnóstico IA (Hypothesis, AIDiagnosis)
    - **Descrição:** Criar modelos para representar diagnóstico gerado pela IA
    - **Critérios de Aceitação:**
      - ✅ Modelo `Hypothesis` com: description (str), probability (str), action (str), related_line (int, opcional)
      - ✅ Modelo `AIDiagnosis` com: summary (str), probable_cause (str), hypotheses (list[Hypothesis])
      - ✅ Validação: hypotheses deve ter mínimo 3 itens
      - ✅ Validação: action em cada Hypothesis não pode ser vazio
      - ✅ Validação: probability deve ser "alta", "média" ou "baixa"
    - **Definition of Done:**
      - [ ] AIDiagnosis rejeita lista com < 3 hypotheses
      - [ ] Hypothesis rejeita action vazio
      - [ ] Hypothesis aceita related_line None
    - **Estimativa:** 1h
    - _Requisitos: RF-05.2, RF-05.3_
  
  - [ ] 2.4 Criar schemas de request/response da API
    - **Descrição:** Criar schemas Pydantic para validação de entrada/saída da API
    - **Critérios de Aceitação:**
      - ✅ `LogFileUpload` valida extensão (.log, .txt)
      - ✅ `LogTextUpload` valida tamanho (max 100.000 caracteres)
      - ✅ `LogTextUpload` valida campo content não vazio
      - ✅ `LogAnalysisResponse` com todos os campos obrigatórios (id, created_at, total_entries, etc)
      - ✅ `LogListParams` com page (≥1) e page_size (≤100)
    - **Definition of Done:**
      - [ ] LogFileUpload rejeita .pdf, .docx
      - [ ] LogTextUpload rejeita content > 100k chars
      - [ ] LogListParams rejeita page=0 ou page_size=101
    - **Estimativa:** 1h
    - _Requisitos: RF-01.1, RF-02.2, RF-07.1_

- [ ] 3. Implementar Parser de Logs com Drain3
  - **Descrição:** Criar componente que transforma logs brutos em estruturas LogEntry usando Drain3 para extração de templates
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `LogParser` com métodos `parse()` e `get_templates()`
    - ✅ `Drain3LogParser` configurado com depth=4 e sim_th=0.4
    - ✅ Reconhece 3 formatos: JSON estruturado, Syslog RFC 3164, texto livre
    - ✅ Normaliza aliases: WARN→WARNING, ERR→ERROR, FATAL→CRITICAL, TRACE→DEBUG
    - ✅ Infere timestamp quando ausente (flag `timestamp_inferred=True`)
    - ✅ Infere level quando ausente (default INFO, flag `level_inferred=True`)
    - ✅ Extrai templates com Drain3 e atribui template_id
    - ✅ Coleta até 5 sample_messages por template
  - **Definition of Done:**
    - [ ] Parser processa log de 1000 linhas sem erros
    - [ ] Linhas malformadas não interrompem processamento (RNF-03)
    - [ ] Parsing de 1 linha < 1ms (RNF-02)
    - [ ] Testes cobrem os 3 formatos + normalização + inferência
  - **Dependências:** Tarefa 2 (modelos LogEntry, LogTemplate)
  - **Estimativa:** 6-8 horas
  - _Requisitos: RF-03.1, RF-03.2, RF-03.3, RF-03.4, RF-03.5, RF-03.6, RNF-02, RNF-03_
  - [ ] 3.1 Criar interface abstrata LogParser
    - **Descrição:** Definir contrato abstrato para implementações de parser
    - **Critérios de Aceitação:**
      - ✅ Classe abstrata `LogParser` com ABC (Abstract Base Class)
      - ✅ Método abstrato `parse(raw_content: str) -> list[LogEntry]`
      - ✅ Método abstrato `get_templates() -> list[LogTemplate]`
      - ✅ Tipagem completa com type hints
    - **Definition of Done:**
      - [ ] Não é possível instanciar LogParser diretamente
      - [ ] Subclasse sem implementar métodos gera erro
      - [ ] mypy --strict passa sem erros
    - **Estimativa:** 30min
    - _Requisitos: RF-03.1_
  
  - [x] 3.2 Implementar Drain3LogParser
    - **Descrição:** Implementar parser concreto usando biblioteca Drain3
    - **Critérios de Aceitação:**
      - ✅ Drain3 configurado com depth=4 e sim_th=0.4
      - ✅ Reconhece formato JSON estruturado ({"timestamp": ..., "level": ..., "message": ...})
      - ✅ Reconhece formato Syslog RFC 3164 (Jan 1 12:00:00 host app[pid]: message)
      - ✅ Fallback para texto livre genérico (cada linha = 1 LogEntry)
      - ✅ Extrai templates com Drain3 para cada formato
    - **Definition of Done:**
      - [ ] Processa JSON válido corretamente
      - [ ] Processa Syslog RFC 3164 corretamente
      - [ ] Processa texto livre sem erros
      - [ ] Templates são extraídos e agrupados
    - **Estimativa:** 3-4h
    - _Requisitos: RF-03.2, RF-03.3_
  
  - [ ] 3.3 Implementar normalização de severidade
    - **Descrição:** Normalizar aliases de severidade para valores padrão
    - **Critérios de Aceitação:**
      - ✅ WARN → WARNING
      - ✅ ERR → ERROR
      - ✅ FATAL → CRITICAL
      - ✅ TRACE → DEBUG
      - ✅ Quando level ausente: atribuir INFO e marcar `level_inferred=True`
      - ✅ Case-insensitive (warn, WARN, Warn → WARNING)
    - **Definition of Done:**
      - [ ] Todos os aliases são normalizados
      - [ ] Level ausente resulta em INFO com flag
      - [ ] Testes cobrem todos os aliases
    - **Estimativa:** 1h
    - _Requisitos: RF-03.4, RF-03.6_
  
  - [ ] 3.4 Implementar inferência de timestamp
    - **Descrição:** Detectar e parsear timestamps em múltiplos formatos
    - **Critérios de Aceitação:**
      - ✅ Detecta ISO 8601 (2024-01-15T10:00:00Z)
      - ✅ Detecta RFC 3339 (2024-01-15 10:00:00+00:00)
      - ✅ Detecta formatos custom (Jan 15 10:00:00, 2024/01/15 10:00:00)
      - ✅ Quando timestamp ausente: usa momento do processamento
      - ✅ Marca `timestamp_inferred=True` quando inferido
    - **Definition of Done:**
      - [ ] Parseia corretamente 3+ formatos de timestamp
      - [ ] Timestamp ausente usa datetime.now()
      - [ ] Flag timestamp_inferred é setada corretamente
    - **Estimativa:** 1-2h
    - _Requisitos: RF-03.5_
  
  - [ ] 3.5 Implementar extração de templates
    - **Descrição:** Usar Drain3 para extrair templates de mensagens similares
    - **Critérios de Aceitação:**
      - ✅ Integra Drain3 para agrupar mensagens similares
      - ✅ Extrai LogTemplate com pattern (ex: "Database timeout <*>")
      - ✅ Atribui template_id único a cada LogEntry
      - ✅ Coleta até 5 sample_messages por template
      - ✅ Conta occurrences (número de vezes que template aparece)
    - **Definition of Done:**
      - [ ] Mensagens similares recebem mesmo template_id
      - [ ] LogTemplate tem pattern com wildcards <*>
      - [ ] sample_messages limitado a 5 exemplos
    - **Estimativa:** 2h
    - _Requisitos: RF-03.1_
  
- [ ] 4. Checkpoint - Validar Parser
  - **Descrição:** Validação intermediária para garantir que o Parser está funcionando corretamente antes de prosseguir
  - **Critérios de Aceitação:**
    - ✅ Todos os testes do Parser (unitários + propriedade) passam
    - ✅ Parser processa logs de exemplo sem erros
    - ✅ Linhas malformadas não interrompem processamento
    - ✅ Templates são extraídos corretamente
  - **Definition of Done:**
    - [ ] `pytest tests/parsers/ -v` passa 100%
    - [ ] Processar `logs/sample_error.log` retorna LogEntry válidos
    - [ ] Cobertura de testes do módulo parsers ≥ 80%
  - **Dependências:** Tarefa 3 (Parser implementado)
  - **Estimativa:** 1 hora (validação)
  - _Requisitos: RF-03.*, RNF-03_

- [x] 5. Implementar Analyzer de Anomalias
  - **Descrição:** Criar componente que detecta anomalias (spikes, stack traces) em um LogStream
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `LogAnalyzer` com método `analyze()`
    - ✅ `AnomalyDetector` agrupa LogEntry por template_id
    - ✅ Calcula distribuição de severidade (contagem por SeverityLevel)
    - ✅ Detecta spikes: ≥10 erros (ERROR/CRITICAL) em janela de 60s
    - ✅ Detecta e agrupa Python traceback, Java stacktrace, Go panic
    - ✅ Retorna `insufficient_data=True` se < 2 entradas
  - **Definition of Done:**
    - [ ] Spike detectado corretamente com 10 erros em 60s
    - [ ] Stack traces multi-linha agrupados em 1 evento
    - [ ] Distribuição de severidade soma 100% das entradas
    - [ ] Testes cobrem casos: 0, 1, 2, 10, 100 entradas
  - **Dependências:** Tarefa 2 (modelos Spike, AnalysisResult), Tarefa 4 (Parser validado)
  - **Estimativa:** 5-6 horas
  - _Requisitos: RF-04.1, RF-04.2, RF-04.3, RF-04.4, RF-04.5, RN-01, RN-02_
  - [ ] 5.1 Criar interface abstrata LogAnalyzer
    - **Descrição:** Definir contrato abstrato para implementações de analyzer
    - **Critérios de Aceitação:**
      - ✅ Classe abstrata `LogAnalyzer` com ABC
      - ✅ Método abstrato `analyze(entries: list[LogEntry], templates: list[LogTemplate]) -> AnalysisResult`
      - ✅ Tipagem completa com type hints
    - **Definition of Done:**
      - [ ] Não é possível instanciar LogAnalyzer diretamente
      - [ ] mypy --strict passa sem erros
    - **Estimativa:** 30min
    - _Requisitos: RF-04.1_
  
  - [ ] 5.2 Implementar AnomalyDetector
    - **Descrição:** Implementar detector de anomalias concreto
    - **Critérios de Aceitação:**
      - ✅ Agrupa LogEntry por template_id
      - ✅ Calcula distribuição de severidade (contagem por SeverityLevel)
      - ✅ Verifica dados insuficientes: se < 2 entradas, retorna `insufficient_data=True`
      - ✅ Retorna AnalysisResult com contadores e distribuição
    - **Definition of Done:**
      - [ ] Agrupamento por template_id funciona
      - [ ] Distribuição soma 100% das entradas
      - [ ] < 2 entradas retorna insufficient_data=True
    - **Estimativa:** 2h
    - _Requisitos: RF-04.1, RF-04.4, RF-04.5_
  
  - [ ] 5.3 Implementar detecção de spikes
    - **Descrição:** Detectar spikes de erros usando janela deslizante
    - **Critérios de Aceitação:**
      - ✅ Janela deslizante de 60 segundos
      - ✅ Detecta spike quando ≥10 erros (ERROR ou CRITICAL) na janela
      - ✅ Cria objetos Spike com: start_time, end_time, error_count
      - ✅ Múltiplos spikes podem ser detectados em um LogStream
    - **Definition of Done:**
      - [ ] Spike detectado com exatamente 10 erros em 60s
      - [ ] Spike detectado com 15 erros em 60s
      - [ ] Não detecta spike com 9 erros em 60s
      - [ ] Não detecta spike com 10 erros em 61s
    - **Estimativa:** 2-3h
    - _Requisitos: RF-04.2, RN-02_
  
  - [ ] 5.4 Implementar agrupamento de stack traces
    - **Descrição:** Detectar e agrupar stack traces multi-linha
    - **Critérios de Aceitação:**
      - ✅ Detecta Python traceback (regex: "Traceback \\(most recent call last\\)")
      - ✅ Detecta Java stacktrace (regex: "Exception in thread|at .*\\(.*\\.java:\\d+\\)")
      - ✅ Detecta Go panic (regex: "panic: |goroutine \\d+")
      - ✅ Agrupa linhas relacionadas em um único evento de erro
      - ✅ Mantém ordem das linhas no agrupamento
    - **Definition of Done:**
      - [ ] Python traceback multi-linha agrupado em 1 evento
      - [ ] Java stacktrace multi-linha agrupado em 1 evento
      - [ ] Go panic multi-linha agrupado em 1 evento
    - **Estimativa:** 2h
    - _Requisitos: RF-04.3_
  
- [-] 6. Implementar AIEngine com Ollama
  - **Descrição:** Criar componente que usa Ollama/LLaMA 3 para gerar diagnóstico inteligente a partir da análise
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `AIEngine` com método `diagnose()`
    - ✅ `OllamaAIEngine` configurado para http://localhost:11434/v1
    - ✅ Amostragem estratificada: 70% erros, 20% warnings, 10% outros (máx 50 entradas)
    - ✅ Prompt do sistema para análise de logs criado
    - ✅ Chamada ao Ollama com modelo llama3 via OpenAI SDK
    - ✅ Timeout de 30s por chamada
    - ✅ Retry com backoff exponencial: 3 tentativas (1s, 2s, 4s)
    - ✅ Verifica disponibilidade do Ollama (porta 11434)
    - ✅ Valida resposta: mínimo 3 hipóteses, cada uma com action não vazio
    - ✅ Lança `AIEngineTimeoutError` após 3 tentativas
    - ✅ Lança `AIEngineUnavailableError` se Ollama indisponível
  - **Definition of Done:**
    - [ ] Diagnóstico gerado com 3+ hipóteses ordenadas por probabilidade
    - [ ] Timeout > 30s retorna HTTP 504
    - [ ] Ollama indisponível retorna HTTP 503
    - [ ] Testes com mock do Ollama cobrem timeout, retry, validação
  - **Dependências:** Tarefa 2 (modelos AIDiagnosis, Hypothesis), Tarefa 5 (Analyzer)
  - **Estimativa:** 6-8 horas
  - _Requisitos: RF-05.1, RF-05.2, RF-05.3, RF-05.5, RF-05.7, RNF-04, RNF-08_
  - [ ] 6.1 Criar interface abstrata AIEngine
    - **Descrição:** Definir contrato abstrato para implementações de AI engine
    - **Critérios de Aceitação:**
      - ✅ Classe abstrata `AIEngine` com ABC
      - ✅ Método abstrato `diagnose(analysis: AnalysisResult, sample_entries: list[LogEntry]) -> AIDiagnosis`
      - ✅ Tipagem completa com type hints
    - **Definition of Done:**
      - [ ] Não é possível instanciar AIEngine diretamente
      - [ ] mypy --strict passa sem erros
    - **Estimativa:** 30min
    - _Requisitos: RF-05.1_
  
  - [ ] 6.2 Implementar OllamaAIEngine
    - **Descrição:** Implementar engine de IA usando Ollama/LLaMA 3
    - **Critérios de Aceitação:**
      - ✅ Cliente OpenAI SDK configurado para http://localhost:11434/v1
      - ✅ Amostragem estratificada: 70% erros, 20% warnings, 10% outros (máx 50 entradas)
      - ✅ Prompt do sistema criado para análise de logs
      - ✅ Chamada ao Ollama com modelo llama3
      - ✅ Resposta parseada para AIDiagnosis
    - **Definition of Done:**
      - [ ] Cliente conecta ao Ollama local
      - [ ] Amostragem respeita proporções
      - [ ] Diagnóstico é gerado com sucesso
    - **Estimativa:** 3h
    - _Requisitos: RF-05.1, RNF-04_
  
  - [ ] 6.3 Implementar timeout e retry com backoff exponencial
    - **Descrição:** Adicionar resiliência com timeout e retry
    - **Critérios de Aceitação:**
      - ✅ Timeout de 30 segundos por chamada
      - ✅ Retry com backoff exponencial: 3 tentativas (1s, 2s, 4s)
      - ✅ Lança `AIEngineTimeoutError` após 3 tentativas falhadas
      - ✅ Log de cada tentativa (tentativa X de 3)
    - **Definition of Done:**
      - [ ] Timeout > 30s lança AIEngineTimeoutError
      - [ ] Retry funciona com backoff correto
      - [ ] Logs mostram tentativas
    - **Estimativa:** 2h
    - _Requisitos: RF-05.7, RNF-08_
  
  - [ ] 6.4 Implementar validação de disponibilidade do Ollama
    - **Descrição:** Verificar se Ollama está disponível antes de processar
    - **Critérios de Aceitação:**
      - ✅ Verifica conectividade com porta 11434 antes de processar
      - ✅ Lança `AIEngineUnavailableError` se Ollama não estiver disponível
      - ✅ Mensagem de erro orienta como iniciar o Ollama
    - **Definition of Done:**
      - [ ] Ollama desligado lança AIEngineUnavailableError
      - [ ] Mensagem de erro é clara e útil
    - **Estimativa:** 1h
    - _Requisitos: RF-05.5_
  
  - [ ] 6.5 Implementar validação de resposta do LLM
    - **Descrição:** Validar resposta do LLM com schema Pydantic
    - **Critérios de Aceitação:**
      - ✅ Valida resposta com schema Pydantic AIDiagnosis
      - ✅ Garante mínimo de 3 hipóteses na resposta
      - ✅ Garante que cada hipótese tem campo action não vazio
      - ✅ Lança ValidationError se resposta inválida
    - **Definition of Done:**
      - [ ] Resposta válida é aceita
      - [ ] Resposta com < 3 hipóteses é rejeitada
      - [ ] Resposta com action vazio é rejeitada
    - **Estimativa:** 1h
    - _Requisitos: RF-05.2, RF-05.3_
  
- [ ] 7. Checkpoint - Validar componentes core
  - **Descrição:** Validação intermediária dos 3 componentes principais (Parser, Analyzer, AIEngine)
  - **Critérios de Aceitação:**
    - ✅ Parser, Analyzer e AIEngine funcionam isoladamente
    - ✅ Todos os testes unitários passam
    - ✅ Testes de integração entre componentes passam
  - **Definition of Done:**
    - [ ] `pytest tests/ -v` passa 100%
    - [ ] Pipeline completo: log bruto → Parser → Analyzer → AIEngine → diagnóstico funciona
    - [ ] Cobertura de testes ≥ 50% nos módulos core
  - **Dependências:** Tarefas 3, 5, 6 (componentes implementados)
  - **Estimativa:** 1-2 horas (validação)
  - _Requisitos: RF-03.*, RF-04.*, RF-05.*_

- [-] 8. Implementar camada de persistência (Repository)
  - **Descrição:** Criar camada de persistência com SQLite para armazenar logs analisados
  - **Critérios de Aceitação:**
    - ✅ Interface abstrata `LogRepository` com métodos CRUD
    - ✅ `SQLiteLogRepository` com schema: logs(id, content, analysis_result, ai_diagnosis, created_at)
    - ✅ Índice em created_at para paginação eficiente
    - ✅ Operações CRUD assíncronas com aiosqlite
    - ✅ Serialização de AnalysisResult e AIDiagnosis como JSON
    - ✅ Transações atômicas com rollback em caso de falha
    - ✅ Context manager para gerenciar transações
  - **Definition of Done:**
    - [ ] `create()` retorna UUID válido
    - [ ] `get_by_id()` com ID inexistente retorna None
    - [ ] `list_paginated()` funciona com diferentes page_size
    - [ ] `delete()` com ID inexistente retorna False
    - [ ] Round-trip: salvar e recuperar log mantém dados intactos
    - [ ] Testes cobrem casos: sucesso, falha, rollback
  - **Dependências:** Tarefa 2 (modelos), Tarefa 7 (componentes core validados)
  - **Estimativa:** 4-5 horas
  - _Requisitos: RF-06.1, RF-06.2, RF-06.3, RF-06.4, RF-06.5, RF-06.6, RNF-01_
  - [ ] 8.1 Criar interface abstrata LogRepository
    - **Descrição:** Definir contrato abstrato para implementações de repository
    - **Critérios de Aceitação:**
      - ✅ Classe abstrata `LogRepository` com ABC
      - ✅ Método `create(content: str, analysis: AnalysisResult, diagnosis: AIDiagnosis) -> str`
      - ✅ Método `get_by_id(log_id: str) -> LogAnalysisResponse | None`
      - ✅ Método `list_paginated(page: int, page_size: int) -> list[LogAnalysisResponse]`
      - ✅ Método `delete(log_id: str) -> bool`
      - ✅ Todos os métodos são abstratos e assíncronos (async)
    - **Definition of Done:**
      - [ ] Não é possível instanciar LogRepository diretamente
      - [ ] mypy --strict passa sem erros
    - **Estimativa:** 30min
    - _Requisitos: RF-06.1, RF-06.2, RF-06.4, RF-06.5_
  
  - [ ] 8.2 Implementar SQLiteLogRepository
    - **Descrição:** Implementar repository concreto com SQLite
    - **Critérios de Aceitação:**
      - ✅ Schema SQL: tabela logs (id UUID, content TEXT, analysis_result JSON, ai_diagnosis JSON, created_at TIMESTAMP)
      - ✅ Índice em created_at para paginação eficiente
      - ✅ Operações CRUD assíncronas com aiosqlite
      - ✅ Serializa AnalysisResult e AIDiagnosis como JSON
      - ✅ Desserializa JSON para objetos Pydantic ao recuperar
    - **Definition of Done:**
      - [ ] Tabela é criada automaticamente se não existir
      - [ ] CRUD funciona corretamente
      - [ ] Round-trip: salvar e recuperar mantém dados intactos
    - **Estimativa:** 3h
    - _Requisitos: RF-06.1, RNF-01_
  
  - [ ] 8.3 Implementar transações atômicas
    - **Descrição:** Garantir atomicidade das operações
    - **Critérios de Aceitação:**
      - ✅ Rollback se qualquer etapa falhar
      - ✅ Context manager para gerenciar transações
      - ✅ Usa `async with` para garantir cleanup
    - **Definition of Done:**
      - [ ] Falha no meio da transação faz rollback
      - [ ] Dados não são persistidos em caso de erro
    - **Estimativa:** 1h
    - _Requisitos: RF-06.1_
  
- [ ] 9. Implementar camada de serviço (Services)
  - **Descrição:** Criar camada de serviço que orquestra o pipeline completo de análise
  - **Critérios de Aceitação:**
    - ✅ `LogAnalysisService.analyze_content()` orquestra: Parser → Analyzer → AIEngine → Repository
    - ✅ Tratamento de erros com exceções customizadas
    - ✅ Transação atômica: só persiste se análise completa for bem-sucedida
    - ✅ `LogStorageService.get_by_id()` retorna log por ID
    - ✅ `LogStorageService.list_logs()` retorna lista paginada
    - ✅ `LogStorageService.delete_log()` remove log por ID
  - **Definition of Done:**
    - [ ] Pipeline completo funciona end-to-end com log válido
    - [ ] Falha no Parser não persiste log
    - [ ] Falha no AIEngine não persiste log
    - [ ] Testes de integração cobrem sucesso e falhas
  - **Dependências:** Tarefas 3, 5, 6, 8 (componentes e repository)
  - **Estimativa:** 3-4 horas
  - _Requisitos: RF-01.5, RF-02.5, RF-06.1, RF-06.2, RF-06.4, RF-06.5_
  - [ ] 9.1 Implementar LogAnalysisService
    - **Descrição:** Orquestrar pipeline completo de análise
    - **Critérios de Aceitação:**
      - ✅ Método `analyze_content(content: str) -> LogAnalysisResponse`
      - ✅ Orquestra pipeline: Parser → Analyzer → AIEngine → Repository
      - ✅ Tratamento de erros com exceções customizadas
      - ✅ Transação atômica: só persiste se análise completa for bem-sucedida
      - ✅ Retorna LogAnalysisResponse com id gerado
    - **Definition of Done:**
      - [ ] Pipeline completo funciona com log válido
      - [ ] Falha no Parser não persiste log
      - [ ] Falha no AIEngine não persiste log
      - [ ] Exceções são propagadas corretamente
    - **Estimativa:** 2-3h
    - _Requisitos: RF-01.5, RF-02.5, RF-06.1_
  
  - [ ] 9.2 Implementar LogStorageService
    - **Descrição:** Serviço para operações de consulta e deleção
    - **Critérios de Aceitação:**
      - ✅ Método `get_by_id(log_id: str) -> LogAnalysisResponse | None`
      - ✅ Método `list_logs(page: int, page_size: int) -> list[LogAnalysisResponse]`
      - ✅ Método `delete_log(log_id: str) -> bool`
      - ✅ Validação de parâmetros (page ≥ 1, page_size ≤ 100)
    - **Definition of Done:**
      - [ ] get_by_id retorna None para ID inexistente
      - [ ] list_logs respeita paginação
      - [ ] delete_log retorna False para ID inexistente
    - **Estimativa:** 1h
    - _Requisitos: RF-06.2, RF-06.4, RF-06.5_
  
- [ ] 10. Implementar endpoints da API (Routers)
  - **Descrição:** Criar todos os endpoints REST da API com FastAPI
  - **Critérios de Aceitação:**
    - ✅ POST /api/v1/logs/file: aceita .log/.txt, max 50MB, retorna HTTP 200/413/415/422
    - ✅ POST /api/v1/logs/text: aceita content, max 100k chars, retorna HTTP 200/413/422
    - ✅ GET /api/v1/logs: paginação (page≥1, page_size≤100), retorna lista
    - ✅ GET /api/v1/logs/{id}: retorna log completo ou HTTP 404
    - ✅ DELETE /api/v1/logs/{id}: remove log, retorna HTTP 204/404
    - ✅ Validação de UUID em path params
    - ✅ Streaming de arquivo com UploadFile
    - ✅ Aceita quebras de linha \n e \r\n
  - **Definition of Done:**
    - [ ] Todos os endpoints retornam JSON válido
    - [ ] Validações Pydantic funcionam (tamanho, formato, campos obrigatórios)
    - [ ] Testes cobrem: sucesso, arquivo grande, formato inválido, ID inexistente
    - [ ] Documentação Swagger acessível em /docs
  - **Dependências:** Tarefas 2, 9 (modelos e services)
  - **Estimativa:** 5-6 horas
  - _Requisitos: RF-01.*, RF-02.*, RF-06.*, RF-07.5_
  - [ ] 10.1 Criar router para POST /api/v1/logs/file
    - **Descrição:** Endpoint para upload de arquivo de log
    - **Critérios de Aceitação:**
      - ✅ Valida formato de arquivo (.log ou .txt)
      - ✅ Valida tamanho máximo (50 MB)
      - ✅ Implementa streaming de arquivo com UploadFile
      - ✅ Retorna HTTP 415 para formato não suportado
      - ✅ Retorna HTTP 413 para arquivo muito grande
      - ✅ Retorna HTTP 422 para arquivo vazio
      - ✅ Retorna HTTP 200 com LogAnalysisResponse em caso de sucesso
    - **Definition of Done:**
      - [ ] Upload de .log funciona
      - [ ] Upload de .txt funciona
      - [ ] Upload de .pdf retorna HTTP 415
      - [ ] Arquivo > 50MB retorna HTTP 413
    - **Estimativa:** 2h
    - _Requisitos: RF-01.1, RF-01.2, RF-01.3, RF-01.4_
  
  - [ ] 10.2 Criar router para POST /api/v1/logs/text
    - **Descrição:** Endpoint para envio de log via texto
    - **Critérios de Aceitação:**
      - ✅ Valida campo content não vazio
      - ✅ Valida tamanho máximo (100.000 caracteres)
      - ✅ Aceita quebras de linha \n e \r\n
      - ✅ Retorna HTTP 422 para content vazio ou ausente
      - ✅ Retorna HTTP 413 para texto muito grande
      - ✅ Retorna HTTP 200 com LogAnalysisResponse em caso de sucesso
    - **Definition of Done:**
      - [ ] Texto válido funciona
      - [ ] Texto vazio retorna HTTP 422
      - [ ] Texto > 100k chars retorna HTTP 413
      - [ ] \n e \r\n são aceitos
    - **Estimativa:** 1h
    - _Requisitos: RF-02.1, RF-02.2, RF-02.3, RF-02.4_
  
  - [ ] 10.3 Criar router para GET /api/v1/logs
    - **Descrição:** Endpoint para listagem paginada de logs
    - **Critérios de Aceitação:**
      - ✅ Implementa paginação com query params page e page_size
      - ✅ Valida page ≥ 1 e page_size ≤ 100
      - ✅ Retorna lista com id, created_at e summary
      - ✅ Retorna HTTP 200 com lista (pode ser vazia)
      - ✅ Retorna HTTP 422 para parâmetros inválidos
    - **Definition of Done:**
      - [ ] Paginação funciona corretamente
      - [ ] page=0 retorna HTTP 422
      - [ ] page_size=101 retorna HTTP 422
    - **Estimativa:** 1h
    - _Requisitos: RF-06.4_
  
  - [ ] 10.4 Criar router para GET /api/v1/logs/{id}
    - **Descrição:** Endpoint para consulta de log por ID
    - **Critérios de Aceitação:**
      - ✅ Valida formato UUID do id
      - ✅ Retorna HTTP 404 se id não existir
      - ✅ Retorna registro completo com análise e diagnóstico
      - ✅ Retorna HTTP 200 com LogAnalysisResponse em caso de sucesso
    - **Definition of Done:**
      - [ ] UUID válido retorna log
      - [ ] UUID inexistente retorna HTTP 404
      - [ ] UUID inválido retorna HTTP 422
    - **Estimativa:** 1h
    - _Requisitos: RF-06.2, RF-06.3_
  
  - [ ] 10.5 Criar router para DELETE /api/v1/logs/{id}
    - **Descrição:** Endpoint para remoção de log por ID
    - **Critérios de Aceitação:**
      - ✅ Valida formato UUID do id
      - ✅ Retorna HTTP 204 se removido com sucesso
      - ✅ Retorna HTTP 404 se id não existir
      - ✅ Retorna HTTP 422 para UUID inválido
    - **Definition of Done:**
      - [ ] UUID válido remove log e retorna HTTP 204
      - [ ] UUID inexistente retorna HTTP 404
      - [ ] UUID inválido retorna HTTP 422
    - **Estimativa:** 1h
    - _Requisitos: RF-06.5, RF-06.6_
  
- [ ] 11. Implementar tratamento de erros e middleware
  - **Descrição:** Criar hierarquia de exceções e middleware para tratamento centralizado de erros
  - **Critérios de Aceitação:**
    - ✅ Hierarquia de exceções: LogPulseError (base), ParsingError, AnalysisError, AIEngineError, StorageError
    - ✅ Exceções específicas: AIEngineTimeoutError, AIEngineUnavailableError
    - ✅ Middleware mapeia exceções para HTTP status codes
    - ✅ Todas as respostas de erro têm campo `detail`
    - ✅ Logging estruturado de erros
  - **Definition of Done:**
    - [ ] ParsingError → HTTP 422
    - [ ] AIEngineTimeoutError → HTTP 504
    - [ ] AIEngineUnavailableError → HTTP 503
    - [ ] StorageError → HTTP 500
    - [ ] Testes cobrem cada tipo de exceção
  - **Dependências:** Tarefa 10 (endpoints implementados)
  - **Estimativa:** 2-3 horas
  - _Requisitos: RF-05.5, RF-05.7, RF-07.4_
  - [ ] 11.1 Criar hierarquia de exceções customizadas
    - **Descrição:** Criar hierarquia de exceções para o sistema
    - **Critérios de Aceitação:**
      - ✅ Classe base `LogPulseError(Exception)`
      - ✅ `ParsingError(LogPulseError)` para erros de parsing
      - ✅ `AnalysisError(LogPulseError)` para erros de análise
      - ✅ `AIEngineError(LogPulseError)` para erros de IA
      - ✅ `AIEngineTimeoutError(AIEngineError)` para timeout
      - ✅ `AIEngineUnavailableError(AIEngineError)` para Ollama indisponível
      - ✅ `StorageError(LogPulseError)` para erros de persistência
    - **Definition of Done:**
      - [ ] Todas as exceções herdam de LogPulseError
      - [ ] Exceções têm mensagens descritivas
    - **Estimativa:** 1h
    - _Requisitos: RF-05.5, RF-05.7_
  
  - [ ] 11.2 Implementar middleware de tratamento de erros
    - **Descrição:** Middleware para capturar e tratar exceções
    - **Critérios de Aceitação:**
      - ✅ Mapeia `ParsingError` → HTTP 422
      - ✅ Mapeia `AIEngineTimeoutError` → HTTP 504
      - ✅ Mapeia `AIEngineUnavailableError` → HTTP 503
      - ✅ Mapeia `StorageError` → HTTP 500
      - ✅ Garante que todas as respostas de erro têm campo `detail`
      - ✅ Implementa logging estruturado de erros
    - **Definition of Done:**
      - [ ] Cada tipo de exceção retorna HTTP status correto
      - [ ] Todas as respostas de erro têm campo detail
      - [ ] Erros são logados com stack trace
    - **Estimativa:** 1-2h
    - _Requisitos: RF-07.4_
  
- [ ] 12. Implementar configuração e inicialização da aplicação
  - **Descrição:** Criar sistema de configuração e aplicação FastAPI principal
  - **Critérios de Aceitação:**
    - ✅ Carregamento de variáveis de ambiente com pydantic-settings
    - ✅ Carregamento de logpulse.toml (local e ~/.config/logpulse/)
    - ✅ Precedência: env vars > local toml > global toml > defaults
    - ✅ Aplicação FastAPI com CORS configurado
    - ✅ Routers registrados com prefixo /api/v1
    - ✅ Swagger UI em /docs e ReDoc em /redoc
    - ✅ Injeção de dependências (Parser, Analyzer, AIEngine, Repository)
    - ✅ Health check endpoint GET /health (verifica API, database, Ollama)
  - **Definition of Done:**
    - [ ] Variáveis de ambiente sobrescrevem TOML
    - [ ] TOML inválido usa configuração padrão (sem crash)
    - [ ] /health retorna "healthy" ou "degraded"
    - [ ] Testes cobrem precedência de configuração
  - **Dependências:** Tarefas 10, 11 (endpoints e tratamento de erros)
  - **Estimativa:** 4-5 horas
  - _Requisitos: RF-07.5, RF-08.1, RF-08.2, RF-08.3, RF-08.4, RNF-05, RNF-08_
  - [ ] 12.1 Criar módulo de configuração
    - **Descrição:** Sistema de configuração com múltiplas fontes
    - **Critérios de Aceitação:**
      - ✅ Carrega variáveis de ambiente com pydantic-settings
      - ✅ Carrega logpulse.toml do diretório local
      - ✅ Carrega logpulse.toml de ~/.config/logpulse/
      - ✅ Precedência: env vars > local toml > global toml > defaults
      - ✅ Usa tomllib (stdlib Python 3.11+) para parsear TOML
    - **Definition of Done:**
      - [ ] Variáveis de ambiente sobrescrevem TOML
      - [ ] TOML local sobrescreve TOML global
      - [ ] TOML inválido usa configuração padrão (sem crash)
    - **Estimativa:** 2h
    - _Requisitos: RF-08.1, RF-08.2, RF-08.3_
  
  - [ ] 12.2 Criar aplicação FastAPI principal
    - **Descrição:** Configurar aplicação FastAPI com routers e docs
    - **Critérios de Aceitação:**
      - ✅ Configura CORS se necessário
      - ✅ Registra routers com prefixo /api/v1
      - ✅ Configura Swagger UI em /docs
      - ✅ Configura ReDoc em /redoc
      - ✅ Adiciona middleware de tratamento de erros
    - **Definition of Done:**
      - [ ] /docs acessível e funcional
      - [ ] /redoc acessível e funcional
      - [ ] Todos os endpoints aparecem na documentação
    - **Estimativa:** 1h
    - _Requisitos: RF-07.5_
  
  - [ ] 12.3 Implementar injeção de dependências
    - **Descrição:** Configurar injeção de dependências do FastAPI
    - **Critérios de Aceitação:**
      - ✅ Factory function para Parser (retorna Drain3LogParser)
      - ✅ Factory function para Analyzer (retorna AnomalyDetector)
      - ✅ Factory function para AIEngine (retorna OllamaAIEngine)
      - ✅ Factory function para Repository (retorna SQLiteLogRepository)
      - ✅ Usa FastAPI Depends para injeção automática
    - **Definition of Done:**
      - [ ] Dependências são injetadas automaticamente nos endpoints
      - [ ] Fácil trocar implementações (ex: MockAIEngine para testes)
    - **Estimativa:** 1h
    - _Requisitos: RNF-05_
  
  - [ ] 12.4 Implementar health check endpoint
    - **Descrição:** Endpoint para verificar saúde do sistema
    - **Critérios de Aceitação:**
      - ✅ GET /health verifica API (sempre healthy)
      - ✅ GET /health verifica database (tenta query simples)
      - ✅ GET /health verifica Ollama (tenta conectar porta 11434)
      - ✅ Retorna status "healthy" se tudo OK
      - ✅ Retorna status "degraded" se algum componente falhar
      - ✅ Retorna detalhes de cada componente
    - **Definition of Done:**
      - [ ] /health retorna "healthy" com tudo funcionando
      - [ ] /health retorna "degraded" com Ollama desligado
      - [ ] Resposta tem detalhes de cada componente
    - **Estimativa:** 1h
    - _Requisitos: RNF-08_
  
- [ ] 13. Checkpoint - Validar aplicação completa
  - **Descrição:** Validação end-to-end da aplicação completa
  - **Critérios de Aceitação:**
    - ✅ Todos os endpoints funcionam end-to-end
    - ✅ Documentação Swagger acessível e funcional
    - ✅ Aplicação funciona com Ollama rodando
    - ✅ Aplicação retorna erro apropriado com Ollama indisponível
  - **Definition of Done:**
    - [ ] `uvicorn src.main:app` inicia sem erros
    - [ ] Swagger UI em http://localhost:8000/docs funciona
    - [ ] Upload de arquivo .log retorna diagnóstico válido
    - [ ] Ollama desligado retorna HTTP 503
  - **Dependências:** Tarefa 12 (aplicação configurada)
  - **Estimativa:** 2 horas (validação)
  - _Requisitos: RF-*, RNF-*_

- [x] 14. Implementar validação de schemas Pydantic
  - **Descrição:** Garantir que todos os schemas Pydantic estão validando corretamente
  - **Critérios de Aceitação:**
    - ✅ Todos os campos obrigatórios são validados
    - ✅ Validações de tipo funcionam (str, int, datetime, etc)
    - ✅ Validações de tamanho funcionam (max_length, ge, le)
    - ✅ Testes de propriedade cobrem validação de schemas
  - **Definition of Done:**
    - [ ] Testes de propriedade passam para todos os schemas
    - [ ] Campos obrigatórios ausentes geram ValidationError
    - [ ] Tipos incorretos geram ValidationError
  - **Dependências:** Tarefa 2 (modelos implementados)
  - **Estimativa:** 2-3 horas
  - _Requisitos: RF-07.1, RF-07.2, RF-07.3_
- [x] 15. Implementar logging estruturado
  - **Descrição:** Configurar sistema de logging estruturado para toda a aplicação
  - **Critérios de Aceitação:**
    - ✅ Logger configurado com nível INFO
    - ✅ Handler para arquivo logpulse.log
    - ✅ Handler para console
    - ✅ Logs em Parser (início/fim, erros)
    - ✅ Logs em Analyzer (spikes detectados)
    - ✅ Logs em AIEngine (chamadas ao Ollama, timeouts)
    - ✅ Logs em Repository (operações CRUD)
  - **Definition of Done:**
    - [ ] Arquivo logpulse.log é criado e populado
    - [ ] Logs aparecem no console durante execução
    - [ ] Logs contêm timestamp, level, módulo, mensagem
  - **Dependências:** Tarefas 3, 5, 6, 8 (componentes implementados)
  - **Estimativa:** 2 horas
  - _Requisitos: RNF-05_
  - [x] 15.1 Configurar logging com formato estruturado
    - **Descrição:** Configurar sistema de logging estruturado
    - **Critérios de Aceitação:**
      - ✅ Logger configurado com nível INFO
      - ✅ Handler para arquivo logpulse.log
      - ✅ Handler para console (stdout)
      - ✅ Formato: timestamp | level | módulo | mensagem
      - ✅ Rotação de logs (max 10MB, 5 backups)
    - **Definition of Done:**
      - [ ] Arquivo logpulse.log é criado
      - [ ] Logs aparecem no console
      - [ ] Formato é consistente
    - **Estimativa:** 1h
    - _Requisitos: RNF-05_
  
  - [x] 15.2 Adicionar logging em componentes críticos
    - **Descrição:** Adicionar logs em pontos estratégicos do sistema
    - **Critérios de Aceitação:**
      - ✅ Parser: log início/fim, número de entradas, erros
      - ✅ Analyzer: log spikes detectados, distribuição de severidade
      - ✅ AIEngine: log chamadas ao Ollama, timeouts, retries
      - ✅ Repository: log operações CRUD (create, get, delete)
      - ✅ API: log requests (método, path, status, duração)
    - **Definition of Done:**
      - [ ] Logs são gerados em cada componente
      - [ ] Logs têm informações úteis para debug
      - [ ] Logs não expõem dados sensíveis
    - **Estimativa:** 1h
    - _Requisitos: RNF-05_

- [ ] 16. Criar documentação e exemplos
  - **Descrição:** Criar documentação completa do projeto e arquivos de exemplo
  - **Critérios de Aceitação:**
    - ✅ README.md com: descrição, instalação, execução, exemplos de uso
    - ✅ logs/sample_error.log com Python traceback
    - ✅ logs/sample_java.log com Java stacktrace
    - ✅ logs/sample_syslog.log com formato Syslog
    - ✅ .env.example com todas as variáveis documentadas
  - **Definition of Done:**
    - [ ] README tem instruções claras de instalação
    - [ ] Exemplos de curl para cada endpoint
    - [ ] Arquivos de exemplo processam sem erros
    - [ ] .env.example tem valores de exemplo válidos
  - **Dependências:** Tarefa 13 (aplicação validada)
  - **Estimativa:** 3-4 horas
  - _Requisitos: RF-03.2, RF-08.3, RNF-07_
  - [ ] 16.1 Criar README.md
    - **Descrição:** Documentação principal do projeto
    - **Critérios de Aceitação:**
      - ✅ Descrição do projeto e objetivos
      - ✅ Instruções de instalação (Python 3.11+, pip, Ollama)
      - ✅ Instruções de execução (uvicorn, variáveis de ambiente)
      - ✅ Exemplos de uso da API (curl para cada endpoint)
      - ✅ Seção de troubleshooting (Ollama indisponível, etc)
    - **Definition of Done:**
      - [ ] README tem todas as seções
      - [ ] Instruções são claras e testadas
      - [ ] Exemplos funcionam
    - **Estimativa:** 2h
    - _Requisitos: RNF-07_
  
  - [ ] 16.2 Criar arquivos de exemplo
    - **Descrição:** Criar arquivos de log de exemplo para testes
    - **Critérios de Aceitação:**
      - ✅ logs/sample_error.log com Python traceback realista
      - ✅ logs/sample_java.log com Java stacktrace realista
      - ✅ logs/sample_syslog.log com formato Syslog RFC 3164
      - ✅ Cada arquivo tem 50-100 linhas
      - ✅ Arquivos contêm erros, warnings e info
    - **Definition of Done:**
      - [ ] Arquivos são processados sem erros
      - [ ] Arquivos geram diagnósticos úteis
    - **Estimativa:** 1h
    - _Requisitos: RF-03.2_
  
  - [ ] 16.3 Criar arquivo .env.example
    - **Descrição:** Template de variáveis de ambiente
    - **Critérios de Aceitação:**
      - ✅ Documenta todas as variáveis de ambiente
      - ✅ Adiciona valores de exemplo
      - ✅ Adiciona comentários explicativos
      - ✅ Variáveis: OLLAMA_URL, DATABASE_PATH, LOG_LEVEL, etc
    - **Definition of Done:**
      - [ ] .env.example tem todas as variáveis
      - [ ] Comentários são claros
      - [ ] Valores de exemplo são válidos
    - **Estimativa:** 30min
    - _Requisitos: RF-08.3_

- [ ] 17. Configurar ferramentas de qualidade de código
  - **Descrição:** Configurar e validar todas as ferramentas de qualidade de código
  - **Critérios de Aceitação:**
    - ✅ mypy configurado em modo strict no pyproject.toml
    - ✅ black configurado (line-length=100)
    - ✅ isort configurado (profile=black)
    - ✅ ruff configurado (select=["E", "F", "I"])
    - ✅ pytest configurado com pytest-asyncio
    - ✅ hypothesis configurado para property-based testing
    - ✅ coverage configurado (min 30%)
  - **Definition of Done:**
    - [ ] `mypy --strict src/` passa sem erros
    - [ ] `black src/ tests/` formata código
    - [ ] `isort src/ tests/` organiza imports
    - [ ] `ruff check src/ tests/` passa sem erros
    - [ ] `pytest --cov=src --cov-report=html` gera relatório
  - **Dependências:** Tarefa 1 (estrutura do projeto)
  - **Estimativa:** 2-3 horas
  - _Requisitos: RNF-05, RNF-06_
  - [ ] 17.1 Configurar mypy em modo strict
    - **Descrição:** Configurar mypy para tipagem estática rigorosa
    - **Critérios de Aceitação:**
      - ✅ Configuração em pyproject.toml seção [tool.mypy]
      - ✅ strict = true
      - ✅ python_version = "3.11"
      - ✅ Garante que todo código passa em mypy --strict
    - **Definition of Done:**
      - [ ] `mypy --strict src/` passa sem erros
      - [ ] Configuração está em pyproject.toml
    - **Estimativa:** 1h
    - _Requisitos: RNF-05_
  
  - [ ] 17.2 Configurar black, isort e ruff
    - **Descrição:** Configurar ferramentas de formatação e linting
    - **Critérios de Aceitação:**
      - ✅ black configurado: line-length = 100
      - ✅ isort configurado: profile = "black"
      - ✅ ruff configurado: select = ["E", "F", "I"]
      - ✅ Formata todo código com black e isort
      - ✅ Garante que todo código passa em ruff
    - **Definition of Done:**
      - [ ] `black src/ tests/` formata código
      - [ ] `isort src/ tests/` organiza imports
      - [ ] `ruff check src/ tests/` passa sem erros
    - **Estimativa:** 1h
    - _Requisitos: RNF-05_
  
  - [ ] 17.3 Configurar pytest e coverage
    - **Descrição:** Configurar framework de testes e cobertura
    - **Critérios de Aceitação:**
      - ✅ pytest configurado em pyproject.toml
      - ✅ pytest-asyncio para testes assíncronos
      - ✅ hypothesis para property-based testing
      - ✅ coverage configurado: min 30%
      - ✅ Gera relatório HTML de cobertura
    - **Definition of Done:**
      - [ ] `pytest tests/` executa todos os testes
      - [ ] `pytest --cov=src --cov-report=html` gera relatório
      - [ ] Configuração está em pyproject.toml
    - **Estimativa:** 1h
    - _Requisitos: RNF-06_

- [x] 18. Validar cobertura de testes
  - **Descrição:** Garantir cobertura mínima de testes e adicionar testes onde necessário
  - **Critérios de Aceitação:**
    - ✅ Cobertura total ≥ 30% (requisito mínimo)
    - ✅ Parser, Analyzer, Repository ≥ 80%
    - ✅ Services, Routers ≥ 50%
    - ✅ Relatório HTML de cobertura gerado
  - **Definition of Done:**
    - [ ] `pytest --cov=src --cov-report=html` mostra ≥ 30%
    - [ ] Módulos críticos têm alta cobertura (≥80%)
    - [ ] Áreas com baixa cobertura identificadas e documentadas
  - **Dependências:** Todas as tarefas de implementação (1-17)
  - **Estimativa:** 4-6 horas
  - _Requisitos: RNF-06_
- [ ] 19. Checkpoint final - Validação completa do sistema
  - **Descrição:** Validação final de todo o sistema antes do release
  - **Critérios de Aceitação:**
    - ✅ Todos os testes (unitários + property-based) passam
    - ✅ Cobertura de testes ≥ 30%
    - ✅ mypy, black, isort, ruff passam sem erros
    - ✅ Aplicação processa diferentes tipos de logs corretamente
    - ✅ Documentação Swagger completa e funcional
    - ✅ README com instruções claras
  - **Definition of Done:**
    - [ ] `pytest tests/ -v` passa 100%
    - [ ] `pytest --cov=src` mostra ≥ 30%
    - [ ] `mypy --strict src/` sem erros
    - [ ] `ruff check src/ tests/` sem erros
    - [ ] Processar logs de exemplo (Python, Java, Syslog) funciona
    - [ ] /docs mostra todos os endpoints documentados
    - [ ] Sistema pronto para uso em produção
  - **Dependências:** Todas as tarefas anteriores (1-18)
  - **Estimativa:** 3-4 horas (validação final)
  - _Requisitos: Todos (RF-*, RNF-*)_

## Notas

- **Tarefas marcadas com `*` são opcionais** e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental do progresso
- Testes de propriedade validam corretude universal com geração automática de inputs
- Testes unitários validam casos específicos e edge cases
- A implementação segue o princípio de separação de responsabilidades (Parser, Analyzer, AIEngine, Repository)
- Todas as operações de I/O são assíncronas para melhor performance
- O sistema é resiliente a falhas (linhas malformadas, Ollama indisponível, timeouts)

---

## Resumo de Estimativas

| Tarefa | Descrição | Estimativa | Dependências |
|--------|-----------|------------|--------------|
| 1 | Configurar estrutura do projeto | 1-2h | Nenhuma |
| 2 | Implementar modelos Pydantic | 3-4h | Tarefa 1 |
| 3 | Implementar Parser com Drain3 | 6-8h | Tarefa 2 |
| 4 | Checkpoint - Validar Parser | 1h | Tarefa 3 |
| 5 | Implementar Analyzer de Anomalias | 5-6h | Tarefas 2, 4 |
| 6 | Implementar AIEngine com Ollama | 6-8h | Tarefas 2, 5 |
| 7 | Checkpoint - Validar componentes core | 1-2h | Tarefas 3, 5, 6 |
| 8 | Implementar Repository (SQLite) | 4-5h | Tarefas 2, 7 |
| 9 | Implementar Services | 3-4h | Tarefas 3, 5, 6, 8 |
| 10 | Implementar endpoints da API | 5-6h | Tarefas 2, 9 |
| 11 | Implementar tratamento de erros | 2-3h | Tarefa 10 |
| 12 | Implementar configuração e inicialização | 4-5h | Tarefas 10, 11 |
| 13 | Checkpoint - Validar aplicação completa | 2h | Tarefa 12 |
| 14 | Implementar validação de schemas | 2-3h | Tarefa 2 |
| 15 | Implementar logging estruturado | 2h | Tarefas 3, 5, 6, 8 |
| 16 | Criar documentação e exemplos | 3-4h | Tarefa 13 |
| 17 | Configurar ferramentas de qualidade | 2-3h | Tarefa 1 |
| 18 | Validar cobertura de testes | 4-6h | Tarefas 1-17 |
| 19 | Checkpoint final - Validação completa | 3-4h | Tarefas 1-18 |

**Estimativa Total:** 60-80 horas (aproximadamente 2-3 semanas para 1 desenvolvedor)

---

## Caminho Crítico

O caminho crítico para o MVP (tarefas obrigatórias em sequência):

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 16 → 19
```

Tarefas que podem ser feitas em paralelo:
- **Tarefa 14** (validação schemas) pode ser feita após Tarefa 2
- **Tarefa 15** (logging) pode ser feita após Tarefas 3, 5, 6, 8
- **Tarefa 17** (qualidade) pode ser feita após Tarefa 1

---

## Critérios de Sucesso do MVP

✅ **Funcionalidades Core:**
- [ ] API REST funcional com 5 endpoints
- [ ] Upload de arquivo .log/.txt funciona
- [ ] Parsing com Drain3 extrai templates
- [ ] Detecção de anomalias (spikes, stack traces)
- [ ] Diagnóstico com IA local (Ollama/LLaMA 3)
- [ ] Persistência em SQLite

✅ **Qualidade:**
- [ ] Cobertura de testes ≥ 30%
- [ ] mypy --strict passa sem erros
- [ ] Documentação Swagger completa

✅ **Performance:**
- [ ] Processa arquivos até 50 MB
- [ ] Parsing < 1ms por linha
- [ ] Timeout de 30s no Ollama

✅ **Resiliência:**
- [ ] Linhas malformadas não interrompem processamento
- [ ] Ollama indisponível retorna HTTP 503
- [ ] Timeout retorna HTTP 504
