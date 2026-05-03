---
inclusion: always
---

# Produto — LogPulse IA

## Visão Geral

Desenvolver uma IA que analisa logs brutos (stacktraces, logs de produção) e fornece diagnóstico inteligente de problemas, sugerindo causas raiz e correções.

## Objetivos

- Reduzir tempo de investigação de incidentes (MTTR)
- Automatizar análise de logs complexos
- Fornecer sugestões acionáveis para desenvolvedores

## Forma de Entrada e Saída

Criar API REST para realizar as validações de logs conforme os objetivos acima destacados. Será disponibilizada a utilização através do FastAPI (Swagger), a fim de facilitar usabilidade e testes. O input de dados poderá ocorrer através de arquivos `.txt` e `.log`, e também poderá ser feito através de texto.

## Endpoints

| Método   | Rota                | Descrição                  |
|----------|---------------------|----------------------------|
| `POST`   | `api/v1/logs/file`  | Envio de log via arquivo   |
| `POST`   | `api/v1/logs/text`  | Envio de log via texto     |
| `DELETE` | `api/v1/logs/{id}`  | Remoção de um log pelo ID  |
| `GET`    | `api/v1/logs`       | Listagem paginada de logs  |
| `GET`    | `api/v1/logs/{id}`  | Consulta de um log pelo ID |

## Funcionalidades Principais

### 1. Análise de Logs
- Receber logs brutos (stacktrace, logs de produção)
- Identificar padrões de erro
- Extrair informações relevantes (timestamp, severity, mensagens)
- Resumir o problema de forma clara

### 2. Diagnóstico Inteligente
- Sugerir causa raiz do erro
- Apontar linha provável do erro no código
- Sugerir correção ou próximos passos

### 3. Execução Local
- Ollama com modelo LLaMA 3 na porta padrão 11434
- Python 3.11+
- pip instalado

### 4. Roadmap (fora do escopo atual)
- Integração com fontes externas de logs (WildFly, Rancher)
- Suporte a múltiplos provedores de LLM (OpenAI, Gemini, Claude)
- Implementação de memória com embeddings
- Monitoramento de logs em tempo real
- Interface web para visualização dos diagnósticos

## Critérios de Sucesso

- Deve aceitar logs via API
- Deve retornar uma resposta estruturada em JSON
- Deve ter resposta coerente, clara e com qualidade técnica
- Deve gerar diagnóstico de causa provável
- Deve propor ação prática
- Deve ter cobertura de testes de 30%
