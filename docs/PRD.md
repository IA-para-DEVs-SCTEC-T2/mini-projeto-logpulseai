# PRD — LogPulse IA

## Visão do Produto

O LogPulse IA é uma API REST que analisa logs brutos (stacktraces, logs de produção) e fornece diagnóstico inteligente de problemas, sugerindo causas raiz e correções utilizando IA local (Ollama + LLaMA 3).

## Problema

Equipes de desenvolvimento gastam tempo excessivo investigando incidentes em produção, lendo logs manualmente e tentando correlacionar eventos. O MTTR (Mean Time To Resolution) é alto porque:

- Logs são volumosos e difíceis de ler
- Padrões de erro se repetem mas não são reconhecidos rapidamente
- Falta contexto para entender a causa raiz

## Solução

Uma API que recebe logs via arquivo ou texto, processa automaticamente e retorna:

1. **Análise estruturada** — distribuição de severidade, spikes de erro, stack traces agrupados
2. **Diagnóstico IA** — causa raiz provável, hipóteses ordenadas por probabilidade, ações sugeridas

## Público-Alvo

- Desenvolvedores backend investigando incidentes
- Equipes de SRE/DevOps em plantão
- Times que precisam de triagem rápida de problemas

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/logs/file` | Upload de arquivo .log/.txt |
| POST | `/api/v1/logs/text` | Envio de log via texto |
| GET | `/api/v1/logs` | Listagem paginada |
| GET | `/api/v1/logs/{id}` | Consulta por ID |
| DELETE | `/api/v1/logs/{id}` | Remoção por ID |
| GET | `/health` | Health check (API + DB + Ollama) |

## Stack Tecnológica

- **Runtime:** Python 3.11+
- **Framework:** FastAPI
- **IA:** Ollama + LLaMA 3 (via OpenAI SDK)
- **Parser:** Drain3
- **Banco:** SQLite (aiosqlite)
- **Validação:** Pydantic v2

## Critérios de Sucesso

- [ ] Aceitar logs via API (arquivo e texto)
- [ ] Retornar resposta JSON estruturada
- [ ] Diagnóstico coerente com causa provável
- [ ] Propor ação prática para cada hipótese
- [ ] Cobertura de testes ≥ 30%
- [ ] CI passando (lint + types + tests)

## Requisitos Não-Funcionais

- Timeout de 30s para chamadas ao Ollama
- Retry com backoff exponencial (3 tentativas)
- Graceful degradation se IA indisponível
- Logs estruturados (structlog + JSON)
- Arquivo máximo: 50MB

## Roadmap

1. **v0.1** — MVP com endpoints básicos e diagnóstico IA ✅
2. **v0.2** — Monitoramento em tempo real (watchdog)
3. **v0.3** — Suporte a múltiplos LLMs (OpenAI, Gemini)
4. **v0.4** — Interface web para visualização
5. **v1.0** — Integração com fontes externas (WildFly, Rancher)
