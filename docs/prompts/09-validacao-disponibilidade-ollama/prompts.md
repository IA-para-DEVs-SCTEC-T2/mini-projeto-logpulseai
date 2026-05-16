# Prompts — Validação de Disponibilidade do Ollama

## Tarefa

**Implementar validação de disponibilidade do Ollama**

- **Issue**: #273
- **Requisito**: RF-05.5
- **Estimativa**: 1h

## Descrição

Verificar se o Ollama está disponível antes de processar requisições de diagnóstico IA.

## Prompts Utilizados

### Prompt 1 — Implementação do módulo health_check

```
Implementar módulo dedicado src/ai/health_check.py com verificação de disponibilidade
do Ollama em duas camadas:
1. Conexão TCP na porta 11434 (rápido, verifica se o processo está rodando)
2. Requisição HTTP GET /api/tags (verifica se a API está respondendo)

Funções:
- check_ollama_tcp(host, port, timeout) → verifica conectividade TCP
- check_ollama_http(base_url, timeout) → verifica API HTTP
- check_ollama_available(host, port, base_url) → verificação completa (TCP + HTTP)

Todas devem lançar AIEngineUnavailableError com mensagem orientando o usuário
a executar "ollama serve".
```

### Prompt 2 — Refatoração do ollama_engine.py

```
Refatorar _check_ollama_availability() em src/ai/ollama_engine.py para delegar
ao novo módulo health_check, mantendo compatibilidade com os testes existentes.
Remover código duplicado de verificação TCP inline.
```

### Prompt 3 — Testes unitários

```
Criar tests/ai/test_health_check.py com cobertura completa:
- TestCheckOllamaTcp: sucesso, conexão recusada, OSError, timeout customizado
- TestCheckOllamaHttp: sucesso, status != 200, ConnectError, TimeoutException
- TestCheckOllamaAvailable: ambos passam, TCP falha, HTTP falha, host/porta customizados
Usar unittest.mock para simular socket e httpx.
```

## Arquivos Criados/Modificados

- `src/ai/health_check.py` — Módulo dedicado de health check (CRIADO)
- `src/ai/ollama_engine.py` — Refatorado para usar health_check
- `src/ai/__init__.py` — Exporta funções de health check
- `tests/ai/test_health_check.py` — 12 testes unitários (CRIADO)
- `pyproject.toml` — Adicionada dependência httpx>=0.25.0

## Resultado dos Testes

- 12 testes novos: ✅ PASSED
- 26 testes existentes (ollama_engine): ✅ PASSED
