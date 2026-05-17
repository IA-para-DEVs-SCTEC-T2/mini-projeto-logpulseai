# Prompts — Implementar OllamaAIEngine

## Tarefa

**Implementar OllamaAIEngine**

- **Issue**: #273
- **Requisitos**: RF-05.1, RNF-04
- **Estimativa**: 3h

## Descrição

Implementar engine de IA usando Ollama/LLaMA 3 via OpenAI SDK (drop-in replacement).

## Prompts Utilizados

### Prompt 1 — Refatoração do construtor

```
Refatorar OllamaAIEngine para aceitar parâmetros configuráveis no construtor:
- base_url: URL base do servidor Ollama (padrão: http://localhost:11434/v1)
- model: Nome do modelo LLM (padrão: llama3)
- timeout: Timeout por chamada em segundos (padrão: 30)

Isso permite configuração flexível sem alterar constantes globais,
facilitando testes e uso com diferentes modelos/servidores.
```

### Prompt 2 — Validação de compatibilidade

```
Garantir que a refatoração mantém compatibilidade com os 26 testes existentes
em tests/ai/test_ollama_engine.py. O construtor sem argumentos deve funcionar
com os mesmos defaults anteriores.
```

## Arquivos Modificados

- `src/ai/ollama_engine.py` — Construtor parametrizável, uso de self._model

## Resultado dos Testes

- 26 testes existentes: ✅ PASSED
