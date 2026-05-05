# Plano de Implementação: LogPulse IA

## Visão Geral

Este documento contém as tarefas de implementação para o LogPulse IA, uma API REST construída com FastAPI que analisa logs brutos e fornece diagnóstico inteligente com IA local (Ollama + LLaMA 3). A implementação segue uma abordagem incremental, com validação contínua através de testes.

## Tarefas

- [ ] 1. Configurar estrutura do projeto e dependências
  - Criar estrutura de pastas (`src/`, `tests/`, `logs/`, `docs/`)
  - Configurar `pyproject.toml` com dependências (FastAPI, Pydantic, Drain3, OpenAI SDK, aiosqlite)
  - Configurar ferramentas de qualidade (mypy, black, isort, ruff)
  - Criar arquivo `.env.example` com variáveis de ambiente 
  - _Requisitos: RNF-05, RNF-07_

- [ ] 2. Implementar modelos de dados com Pydantic
  - [ ] 2.1 Criar modelos base (SeverityLevel, LogEntry, LogTemplate)
    - Implementar enum `SeverityLevel` com valores DEBUG, INFO, WARNING, ERROR, CRITICAL
    - Implementar modelo `LogEntry` com campos timestamp, level, message, raw_line, template_id, flags de inferência
    - Implementar modelo `LogTemplate` com pattern, occurrences e sample_messages
    - _Requisitos: RF-03.1, RF-03.4_
  
  - [ ] 2.2 Criar modelos de análise (Spike, AnalysisResult)
    - Implementar modelo `Spike` com start_time, end_time, error_count, severity
    - Implementar modelo `AnalysisResult` com contadores, spikes, templates e distribuição de severidade
    - _Requisitos: RF-04.2, RF-04.4_
  
  - [ ] 2.3 Criar modelos de diagnóstico IA (Hypothesis, AIDiagnosis)
    - Implementar modelo `Hypothesis` com description, probability, action, related_line
    - Implementar modelo `AIDiagnosis` com summary, probable_cause e lista de hypotheses (mínimo 3)
    - _Requisitos: RF-05.2, RF-05.3_
  
  - [ ] 2.4 Criar schemas de request/response da API
    - Implementar `LogFileUpload` com validação de extensão (.log, .txt)
    - Implementar `LogTextUpload` com validação de tamanho (max 100.000 caracteres)
    - Implementar `LogAnalysisResponse` com todos os campos obrigatórios
    - Implementar `LogListParams` para paginação
    - _Requisitos: RF-01.1, RF-02.2, RF-07.1_

- [ ] 3. Implementar Parser de Logs com Drain3
  - [ ] 3.1 Criar interface abstrata LogParser
    - Definir método abstrato `parse(raw_content: str) -> list[LogEntry]`
    - Definir método abstrato `get_templates() -> list[LogTemplate]`
    - _Requisitos: RF-03.1_
  
  - [ ] 3.2 Implementar Drain3LogParser
    - Configurar Drain3 com depth=4 e sim_th=0.4
    - Implementar parsing de formato JSON estruturado
    - Implementar parsing de formato Syslog RFC 3164
    - Implementar fallback para texto livre genérico
    - _Requisitos: RF-03.2, RF-03.3_
  
  - [ ] 3.3 Implementar normalização de severidade
    - Normalizar aliases: WARN→WARNING, ERR→ERROR, FATAL→CRITICAL, TRACE→DEBUG
    - Implementar inferência de level com flag `level_inferred=True` quando ausente
    - _Requisitos: RF-03.4, RF-03.6_
  
  - [ ] 3.4 Implementar inferência de timestamp
    - Detectar e parsear timestamps em múltiplos formatos (ISO 8601, RFC 3339, custom)
    - Usar timestamp de processamento quando ausente, com flag `timestamp_inferred=True`
    - _Requisitos: RF-03.5_
  
  - [ ] 3.5 Implementar extração de templates
    - Integrar Drain3 para extrair LogTemplate de mensagens similares
    - Atribuir template_id a cada LogEntry
    - Coletar sample_messages (máximo 5) por template
    - _Requisitos: RF-03.1_
  
  - [ ]* 3.6 Escrever testes de propriedade para o Parser
    - **Propriedade 5: Extração de Templates**
    - **Valida: Requisitos RF-03.1**
  
  - [ ]* 3.7 Escrever testes de propriedade para reconhecimento de formatos
    - **Propriedade 6: Reconhecimento de Formatos**
    - **Valida: Requisitos RF-03.2**
  
  - [ ]* 3.8 Escrever testes de propriedade para normalização
    - **Propriedade 8: Normalização de Aliases de Severidade**
    - **Valida: Requisitos RF-03.4**
  
  - [ ]* 3.9 Escrever testes unitários para casos específicos
    - Testar parsing de JSON estruturado válido
    - Testar parsing de Syslog RFC 3164 válido
    - Testar fallback para texto livre
    - Testar linhas malformadas (não deve lançar exceção)
    - _Requisitos: RF-03.2, RF-03.3, RNF-03_

- [ ] 4. Checkpoint - Validar Parser
  - Garantir que todos os testes do Parser passam
  - Verificar que linhas malformadas não interrompem processamento
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [ ] 5. Implementar Analyzer de Anomalias
  - [ ] 5.1 Criar interface abstrata LogAnalyzer
    - Definir método abstrato `analyze(entries: list[LogEntry], templates: list[LogTemplate]) -> AnalysisResult`
    - _Requisitos: RF-04.1_
  
  - [ ] 5.2 Implementar AnomalyDetector
    - Implementar agrupamento de LogEntry por template_id
    - Calcular distribuição de severidade (contagem por SeverityLevel)
    - Implementar verificação de dados insuficientes (< 2 entradas)
    - _Requisitos: RF-04.1, RF-04.4, RF-04.5_
  
  - [ ] 5.3 Implementar detecção de spikes
    - Implementar janela deslizante de 60 segundos
    - Detectar spikes quando ≥10 erros (ERROR ou CRITICAL) na janela
    - Criar objetos Spike com start_time, end_time, error_count
    - _Requisitos: RF-04.2, RN-02_
  
  - [ ] 5.4 Implementar agrupamento de stack traces
    - Detectar Python traceback com regex
    - Detectar Java stacktrace com regex
    - Detectar Go panic com regex
    - Agrupar linhas relacionadas em um único evento de erro
    - _Requisitos: RF-04.3_
  
  - [ ]* 5.5 Escrever testes de propriedade para detecção de spikes
    - **Propriedade 12: Detecção de Spikes**
    - **Valida: Requisitos RF-04.2**
  
  - [ ]* 5.6 Escrever testes de propriedade para distribuição de severidade
    - **Propriedade 14: Invariante de Distribuição de Severidade**
    - **Valida: Requisitos RF-04.4**
  
  - [ ]* 5.7 Escrever testes unitários para casos específicos
    - Testar detecção de spike com exatamente 10 erros em 60s
    - Testar agrupamento de Python traceback multi-linha
    - Testar agrupamento de Java stacktrace multi-linha
    - Testar LogStream com 0, 1, 2 entradas (insufficient_data)
    - _Requisitos: RF-04.2, RF-04.3, RF-04.5_

- [ ] 6. Implementar AIEngine com Ollama
  - [ ] 6.1 Criar interface abstrata AIEngine
    - Definir método abstrato `diagnose(analysis: AnalysisResult, sample_entries: list[LogEntry]) -> AIDiagnosis`
    - _Requisitos: RF-05.1_
  
  - [ ] 6.2 Implementar OllamaAIEngine
    - Configurar cliente OpenAI SDK apontando para http://localhost:11434/v1
    - Implementar amostragem estratificada de entradas (70% erros, 20% warnings, 10% outros, máx 50)
    - Criar prompt do sistema para análise de logs
    - Implementar chamada ao Ollama com modelo llama3
    - _Requisitos: RF-05.1, RNF-04_
  
  - [ ] 6.3 Implementar timeout e retry com backoff exponencial
    - Adicionar timeout de 30 segundos por chamada
    - Implementar retry com backoff exponencial (3 tentativas: 1s, 2s, 4s)
    - Lançar AIEngineTimeoutError após 3 tentativas
    - _Requisitos: RF-05.7, RNF-08_
  
  - [ ] 6.4 Implementar validação de disponibilidade do Ollama
    - Verificar conectividade com porta 11434 antes de processar
    - Lançar AIEngineUnavailableError se Ollama não estiver disponível
    - _Requisitos: RF-05.5_
  
  - [ ] 6.5 Implementar validação de resposta do LLM
    - Validar resposta com schema Pydantic AIDiagnosis
    - Garantir mínimo de 3 hipóteses na resposta
    - Garantir que cada hipótese tem campo action não vazio
    - _Requisitos: RF-05.2, RF-05.3_
  
  - [ ]* 6.6 Escrever testes de propriedade para estrutura de hipóteses
    - **Propriedade 15: Estrutura de Hipóteses**
    - **Valida: Requisitos RF-05.2**
  
  - [ ]* 6.7 Escrever testes de propriedade para completude de ações
    - **Propriedade 16: Completude de Ações**
    - **Valida: Requisitos RF-05.3**
  
  - [ ]* 6.8 Escrever testes unitários com mock do Ollama
    - Testar timeout (> 30s) retorna HTTP 504
    - Testar Ollama indisponível retorna HTTP 503
    - Testar retry com backoff exponencial
    - Testar validação de resposta do LLM
    - _Requisitos: RF-05.5, RF-05.7_

- [ ] 7. Checkpoint - Validar componentes core
  - Garantir que Parser, Analyzer e AIEngine funcionam isoladamente
  - Verificar que todos os testes passam
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [ ] 8. Implementar camada de persistência (Repository)
  - [ ] 8.1 Criar interface abstrata LogRepository
    - Definir método `create(content: str, analysis: AnalysisResult, diagnosis: AIDiagnosis) -> str`
    - Definir método `get_by_id(log_id: str) -> LogAnalysisResponse | None`
    - Definir método `list_paginated(page: int, page_size: int) -> list[LogAnalysisResponse]`
    - Definir método `delete(log_id: str) -> bool`
    - _Requisitos: RF-06.1, RF-06.2, RF-06.4, RF-06.5_
  
  - [ ] 8.2 Implementar SQLiteLogRepository
    - Criar schema SQL com tabela logs (id, content, analysis_result, ai_diagnosis, created_at)
    - Criar índice em created_at para paginação eficiente
    - Implementar operações CRUD com aiosqlite (assíncrono)
    - Serializar AnalysisResult e AIDiagnosis como JSON
    - _Requisitos: RF-06.1, RNF-01_
  
  - [ ] 8.3 Implementar transações atômicas
    - Garantir rollback se qualquer etapa falhar
    - Usar context manager para gerenciar transações
    - _Requisitos: RF-06.1_
  
  - [ ]* 8.4 Escrever testes de propriedade para round-trip
    - **Propriedade 2: Round-Trip de Persistência**
    - **Valida: Requisitos RF-01.5, RF-02.5, RF-06.1, RF-06.2**
  
  - [ ]* 8.5 Escrever testes de propriedade para paginação
    - **Propriedade 17: Paginação Completa**
    - **Valida: Requisitos RF-06.4**
  
  - [ ]* 8.6 Escrever testes de propriedade para deleção
    - **Propriedade 18: Deleção Efetiva**
    - **Valida: Requisitos RF-06.5**
  
  - [ ]* 8.7 Escrever testes unitários para Repository
    - Testar criação de log retorna UUID válido
    - Testar get_by_id com ID inexistente retorna None
    - Testar list_paginated com diferentes page_size
    - Testar delete com ID inexistente retorna False
    - _Requisitos: RF-06.2, RF-06.3, RF-06.6_

- [ ] 9. Implementar camada de serviço (Services)
  - [ ] 9.1 Implementar LogAnalysisService
    - Criar método `analyze_content(content: str) -> LogAnalysisResponse`
    - Orquestrar pipeline: Parser → Analyzer → AIEngine → Repository
    - Implementar tratamento de erros com exceções customizadas
    - Garantir transação atômica (só persiste se análise completa for bem-sucedida)
    - _Requisitos: RF-01.5, RF-02.5, RF-06.1_
  
  - [ ] 9.2 Implementar LogStorageService
    - Criar método `get_by_id(log_id: str) -> LogAnalysisResponse | None`
    - Criar método `list_logs(page: int, page_size: int) -> list[LogAnalysisResponse]`
    - Criar método `delete_log(log_id: str) -> bool`
    - _Requisitos: RF-06.2, RF-06.4, RF-06.5_
  
  - [ ]* 9.3 Escrever testes de integração para Services
    - Testar pipeline completo com log válido
    - Testar falha no Parser não persiste log
    - Testar falha no AIEngine não persiste log
    - _Requisitos: RF-01.5, RF-02.5, RF-06.1_

- [ ] 10. Implementar endpoints da API (Routers)
  - [ ] 10.1 Criar router para POST /api/v1/logs/file
    - Validar formato de arquivo (.log ou .txt)
    - Validar tamanho máximo (50 MB)
    - Implementar streaming de arquivo com UploadFile
    - Retornar HTTP 415 para formato não suportado
    - Retornar HTTP 413 para arquivo muito grande
    - Retornar HTTP 422 para arquivo vazio
    - _Requisitos: RF-01.1, RF-01.2, RF-01.3, RF-01.4_
  
  - [ ] 10.2 Criar router para POST /api/v1/logs/text
    - Validar campo content não vazio
    - Validar tamanho máximo (100.000 caracteres)
    - Aceitar quebras de linha \n e \r\n
    - Retornar HTTP 422 para content vazio ou ausente
    - Retornar HTTP 413 para texto muito grande
    - _Requisitos: RF-02.1, RF-02.2, RF-02.3, RF-02.4_
  
  - [ ] 10.3 Criar router para GET /api/v1/logs
    - Implementar paginação com query params page e page_size
    - Validar page ≥ 1 e page_size ≤ 100
    - Retornar lista com id, created_at e summary
    - _Requisitos: RF-06.4_
  
  - [ ] 10.4 Criar router para GET /api/v1/logs/{id}
    - Validar formato UUID do id
    - Retornar HTTP 404 se id não existir
    - Retornar registro completo com análise e diagnóstico
    - _Requisitos: RF-06.2, RF-06.3_
  
  - [ ] 10.5 Criar router para DELETE /api/v1/logs/{id}
    - Validar formato UUID do id
    - Retornar HTTP 204 se removido com sucesso
    - Retornar HTTP 404 se id não existir
    - _Requisitos: RF-06.5, RF-06.6_
  
  - [ ]* 10.6 Escrever testes de propriedade para validação de entrada
    - **Propriedade 1: Validação de Formato de Arquivo**
    - **Valida: Requisitos RF-01.1, RF-01.4**
  
  - [ ]* 10.7 Escrever testes de propriedade para processamento de texto
    - **Propriedade 3: Processamento de Texto Válido**
    - **Valida: Requisitos RF-02.1**
  
  - [ ]* 10.8 Escrever testes de propriedade para quebras de linha
    - **Propriedade 4: Normalização de Quebras de Linha**
    - **Valida: Requisitos RF-02.4**
  
  - [ ]* 10.9 Escrever testes unitários para endpoints
    - Testar POST /api/v1/logs/file com arquivo válido retorna HTTP 200
    - Testar POST /api/v1/logs/file com arquivo > 50MB retorna HTTP 413
    - Testar POST /api/v1/logs/text com texto vazio retorna HTTP 422
    - Testar GET /api/v1/logs/{id} com ID inexistente retorna HTTP 404
    - Testar DELETE /api/v1/logs/{id} com ID válido retorna HTTP 204
    - _Requisitos: RF-01.2, RF-01.3, RF-02.2, RF-06.3, RF-06.5_

- [ ] 11. Implementar tratamento de erros e middleware
  - [ ] 11.1 Criar hierarquia de exceções customizadas
    - Criar LogPulseError (base)
    - Criar ParsingError, AnalysisError, AIEngineError, StorageError
    - Criar AIEngineTimeoutError e AIEngineUnavailableError
    - _Requisitos: RF-05.5, RF-05.7_
  
  - [ ] 11.2 Implementar middleware de tratamento de erros
    - Mapear exceções para HTTP status codes
    - Garantir que todas as respostas de erro têm campo detail
    - Implementar logging estruturado de erros
    - _Requisitos: RF-07.4_
  
  - [ ]* 11.3 Escrever testes de propriedade para estrutura de erros
    - **Propriedade 21: Presença de Detalhes em Erros**
    - **Valida: Requisitos RF-07.4**
  
  - [ ]* 11.4 Escrever testes unitários para tratamento de erros
    - Testar ParsingError retorna HTTP 422
    - Testar AIEngineTimeoutError retorna HTTP 504
    - Testar AIEngineUnavailableError retorna HTTP 503
    - Testar StorageError retorna HTTP 500
    - _Requisitos: RF-05.5, RF-05.7_

- [ ] 12. Implementar configuração e inicialização da aplicação
  - [ ] 12.1 Criar módulo de configuração
    - Implementar carregamento de variáveis de ambiente com pydantic-settings
    - Implementar carregamento de logpulse.toml (local e ~/.config/logpulse/)
    - Implementar precedência: env vars > local toml > global toml > defaults
    - _Requisitos: RF-08.1, RF-08.2, RF-08.3_
  
  - [ ] 12.2 Criar aplicação FastAPI principal
    - Configurar CORS se necessário
    - Registrar routers com prefixo /api/v1
    - Configurar documentação Swagger UI em /docs
    - Configurar documentação ReDoc em /redoc
    - _Requisitos: RF-07.5_
  
  - [ ] 12.3 Implementar injeção de dependências
    - Criar factory functions para Parser, Analyzer, AIEngine, Repository
    - Configurar FastAPI Depends para injeção automática
    - _Requisitos: RNF-05_
  
  - [ ] 12.4 Implementar health check endpoint
    - Criar GET /health verificando API, database e Ollama
    - Retornar status "healthy" ou "degraded"
    - _Requisitos: RNF-08_
  
  - [ ]* 12.5 Escrever testes unitários para configuração
    - Testar carregamento de .env
    - Testar carregamento de logpulse.toml
    - Testar precedência de variáveis de ambiente
    - Testar TOML inválido usa configuração padrão
    - _Requisitos: RF-08.1, RF-08.2, RF-08.3, RF-08.4_

- [ ] 13. Checkpoint - Validar aplicação completa
  - Garantir que todos os endpoints funcionam end-to-end
  - Verificar que documentação Swagger está acessível
  - Testar com Ollama rodando e indisponível
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

- [ ] 14. Implementar validação de schemas Pydantic
  - [ ]* 14.1 Escrever testes de propriedade para validação de schemas
    - **Propriedade 20: Validação de Schemas Pydantic**
    - **Valida: Requisitos RF-07.2**
  
  - [ ]* 14.2 Escrever testes de propriedade para completude de campos
    - **Propriedade 19: Completude de Campos Obrigatórios**
    - **Valida: Requisitos RF-07.1, RF-07.3**

- [ ] 15. Implementar logging estruturado
  - [ ] 15.1 Configurar logging com formato estruturado
    - Configurar logger com nível INFO
    - Adicionar handler para arquivo logpulse.log
    - Adicionar handler para console
    - _Requisitos: RNF-05_
  
  - [ ] 15.2 Adicionar logging em componentes críticos
    - Adicionar logs em Parser (início/fim, erros)
    - Adicionar logs em Analyzer (spikes detectados)
    - Adicionar logs em AIEngine (chamadas ao Ollama, timeouts)
    - Adicionar logs em Repository (operações CRUD)
    - _Requisitos: RNF-05_

- [ ] 16. Criar documentação e exemplos
  - [ ] 16.1 Criar README.md
    - Adicionar descrição do projeto
    - Adicionar instruções de instalação
    - Adicionar instruções de execução
    - Adicionar exemplos de uso da API
    - _Requisitos: RNF-07_
  
  - [ ] 16.2 Criar arquivos de exemplo
    - Criar logs/sample_error.log com Python traceback
    - Criar logs/sample_java.log com Java stacktrace
    - Criar logs/sample_syslog.log com formato Syslog
    - _Requisitos: RF-03.2_
  
  - [ ] 16.3 Criar arquivo .env.example
    - Documentar todas as variáveis de ambiente
    - Adicionar valores de exemplo
    - _Requisitos: RF-08.3_

- [ ] 17. Configurar ferramentas de qualidade de código
  - [ ] 17.1 Configurar mypy em modo strict
    - Criar configuração em pyproject.toml
    - Garantir que todo código passa em mypy --strict
    - _Requisitos: RNF-05_
  
  - [ ] 17.2 Configurar black, isort e ruff
    - Criar configuração em pyproject.toml
    - Formatar todo código com black e isort
    - Garantir que todo código passa em ruff
    - _Requisitos: RNF-05_
  
  - [ ] 17.3 Configurar pytest e coverage
    - Criar configuração em pyproject.toml
    - Configurar pytest-asyncio para testes assíncronos
    - Configurar hypothesis para property-based testing
    - _Requisitos: RNF-06_

- [ ] 18. Validar cobertura de testes
  - [ ]* 18.1 Executar todos os testes e verificar cobertura
    - Executar pytest --cov=src --cov-report=html
    - Garantir cobertura mínima de 30%
    - Identificar áreas com baixa cobertura
    - _Requisitos: RNF-06_
  
  - [ ]* 18.2 Adicionar testes para áreas com baixa cobertura
    - Priorizar Parser, Analyzer e Repository (>80%)
    - Adicionar testes para Services e Routers (>50%)
    - _Requisitos: RNF-06_

- [ ] 19. Checkpoint final - Validação completa do sistema
  - Executar todos os testes (unitários e property-based)
  - Verificar cobertura de testes ≥ 30%
  - Verificar que mypy, black, isort e ruff passam sem erros
  - Testar aplicação manualmente com diferentes tipos de logs
  - Validar documentação Swagger em /docs
  - Perguntar ao usuário se o sistema está pronto para uso

## Notas

- **Tarefas marcadas com `*` são opcionais** e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental do progresso
- Testes de propriedade validam corretude universal com geração automática de inputs
- Testes unitários validam casos específicos e edge cases
- A implementação segue o princípio de separação de responsabilidades (Parser, Analyzer, AIEngine, Repository)
- Todas as operações de I/O são assíncronas para melhor performance
- O sistema é resiliente a falhas (linhas malformadas, Ollama indisponível, timeouts)
