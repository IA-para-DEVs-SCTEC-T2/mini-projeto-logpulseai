# Prompts — Camada de Serviço (Services)

## Tarefa

**Implementar camada de serviço (Services)**

- **Spec**: logpulse-ia
- **Estimativa**: 3-4 horas
- **Requisitos**: RF-01.5, RF-02.5, RF-06.1, RF-06.2, RF-06.4, RF-06.5

## Descrição

Criar camada de serviço que orquestra o pipeline completo de análise de logs.

## Critérios de Aceitação

- ✅ LogAnalysisService.analyze_content() orquestra: Parser → Analyzer → AIEngine → Repository
- ✅ Tratamento de erros com exceções customizadas
- ✅ Transação atômica: só persiste se análise completa for bem-sucedida
- ✅ LogStorageService.get_by_id() retorna log por ID
- ✅ LogStorageService.list_logs() retorna lista paginada
- ✅ LogStorageService.delete_log() remove log por ID

## Prompts Utilizados

### Prompt 1 — LogAnalysisService

```
Criar src/services/log_analysis_service.py com classe LogAnalysisService que:
- Recebe parser, analyzer, ai_engine e repository via injeção de dependências
- Método async analyze_content(content: str) → LogAnalysisResponse
- Pipeline sequencial: parse → analyze → diagnose → persist
- Transação atômica: só chama repository.create() se todas as etapas anteriores
  forem bem-sucedidas
- Tratamento de erros: cada etapa encapsula exceções genéricas na exceção
  customizada correspondente (ParsingError, AnalysisError, AIEngineError, StorageError)
- Exceções do domínio (AIEngineUnavailableError, etc.) são propagadas sem wrapping
```

### Prompt 2 — LogStorageService

```
Criar src/services/log_storage_service.py com classe LogStorageService que:
- Recebe repository via injeção de dependências
- get_by_id(log_id) → Optional[LogAnalysisResponse]
- list_logs(page, page_size) → LogListResponse com metadados de paginação
- delete_log(log_id) → bool
- Validação de parâmetros (page >= 1, 1 <= page_size <= 100)
- Cálculo de total de páginas
- Tratamento de erros com StorageError
```

### Prompt 3 — Testes unitários

```
Criar testes completos para ambos os serviços:
- tests/services/test_log_analysis_service.py:
  - Pipeline completo com sucesso
  - Transação atômica (não persiste se AI ou Analyzer falham)
  - Tratamento de cada tipo de erro
  - Propagação de exceções do domínio
- tests/services/test_log_storage_service.py:
  - CRUD operations (get, list, delete)
  - Paginação e cálculo de páginas
  - Validação de parâmetros
  - Tratamento de erros
Usar AsyncMock para operações assíncronas do repositório.
```

## Arquivos Criados

- `src/services/__init__.py` — Exporta serviços
- `src/services/log_analysis_service.py` — Serviço de análise (pipeline)
- `src/services/log_storage_service.py` — Serviço de storage (CRUD)
- `tests/services/__init__.py` — Pacote de testes
- `tests/services/test_log_analysis_service.py` — 11 testes
- `tests/services/test_log_storage_service.py` — 15 testes

## Resultado dos Testes

- 26 testes: ✅ PASSED
