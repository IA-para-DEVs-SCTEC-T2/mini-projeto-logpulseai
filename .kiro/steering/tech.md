---
inclusion: always
---

# Tecnologia — LogPulse IA

## Stack

- **Linguagem:** Python 3.11+
- **Gerenciador de pacotes:** `pip`
- **Framework:** FastAPI
- **Banco de dados:** SQLite
- **LLM local:** Ollama com modelo LLaMA 3 (porta padrão 11434)
- **SDK de IA:** OpenAI Python SDK (usado como drop-in replacement apontando para o servidor local do Ollama)
- **Parsing de logs:** Drain3 — biblioteca Python para converter logs em templates
- **Validação:** Pydantic (validação de schemas e payload)
- **Testes:** cobertura mínima de 30%

## Arquitetura

O sistema expõe uma API REST via FastAPI. O fluxo principal é:

```
Input (arquivo .txt/.log ou texto) → API REST → Parser (Drain3) → LLM (Ollama/LLaMA 3) → Diagnóstico JSON
```

## Modelo de Resposta

Todas as respostas da API devem ser estruturadas em JSON, contendo:
- Resumo do problema identificado
- Causa raiz provável
- Linha provável do erro no código
- Sugestão de correção ou próximos passos

## Convenções de Código

- Tipagem com Pydantic para todos os schemas de entrada e saída
- Docstrings em português para funções e classes públicas
- Nomes de variáveis e funções em inglês (`snake_case`)
- Classes em `PascalCase`
- Testes espelham a estrutura de `src/` dentro de `tests/`
- Cobertura mínima de testes: 30%
