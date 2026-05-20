# LogPulse IA

> Analise logs de produção e receba diagnóstico inteligente com causa raiz e ações corretivas.

## Objetivo

O **LogPulse IA** é uma API REST construída com FastAPI que recebe logs brutos (stacktraces, logs de produção), detecta anomalias automaticamente e gera diagnóstico inteligente via IA local (Ollama + LLaMA 3), sem dependência de APIs externas pagas.

## Como rodar

**Pré-requisitos:** Python 3.11+, pip, [Ollama](https://ollama.com) instalado e rodando com o modelo `llama3`.

```bash
# 1. Instalar dependências
pip install -e ".[dev]"

# 2. Iniciar o servidor
uvicorn src.api.app:app --reload --port 8000
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

## Endpoints

| Método   | Rota                    | Descrição                        |
|----------|-------------------------|----------------------------------|
| `POST`   | `/api/v1/logs/file`     | Envio de log via arquivo (.log/.txt, máx 50MB) |
| `POST`   | `/api/v1/logs/text`     | Envio de log via texto (máx 100k chars) |
| `GET`    | `/api/v1/logs`          | Listagem paginada de análises    |
| `GET`    | `/api/v1/logs/{id}`     | Consulta de análise pelo ID      |
| `DELETE` | `/api/v1/logs/{id}`     | Remoção de uma análise pelo ID   |
| `GET`    | `/health`               | Health check da API              |

## Exemplo de resposta

```json
{
  "id": "uuid-gerado",
  "analyzed_at": "2024-01-15T10:00:00Z",
  "metrics": {
    "total_logs": 128,
    "errors": 17,
    "criticals": 6
  },
  "issues": [
    {
      "title": "Database connection pool exhausted",
      "severity": "high",
      "occurrences": 12,
      "first_seen": "2024-01-15T09:58:00Z",
      "last_seen": "2024-01-15T10:00:00Z",
      "recommendation": "Aumentar pool de conexões do banco de dados e revisar connection leaks"
    }
  ],
  "recommended_actions": [
    "Aumentar pool de conexões do banco de dados",
    "Verificar configuração de max_connections"
  ],
  "confidence": 0.85
}
```

## Estrutura do Projeto

```
logpulse-ia/
├── src/
│   ├── api/              # Camada HTTP (FastAPI, routers, middleware)
│   │   └── v1/
│   │       └── routes/   # Handlers dos endpoints
│   ├── services/         # Lógica de negócio (orquestração do pipeline)
│   ├── parsers/          # Parsing de logs com Drain3
│   ├── ai/               # Integração com Ollama/LLaMA 3
│   ├── analyzer/         # Detecção de anomalias e spikes
│   ├── models/           # Schemas Pydantic
│   ├── repository/       # Persistência SQLite
│   └── core/             # Configurações, logging, dependências
├── tests/                # Testes automatizados (cobertura mínima 30%)
├── logs/fixtures/        # Arquivos de log para testes
├── docs/                 # Documentação adicional
└── README.md
```

## Tecnologias

| Componente   | Tecnologia                                    |
|--------------|-----------------------------------------------|
| API          | FastAPI + Pydantic v2                         |
| IA           | Ollama + LLaMA 3 via OpenAI SDK (drop-in)     |
| Parsing      | Drain3 (extração de templates)                |
| Persistência | SQLite + aiosqlite (async)                    |
| Testes       | pytest + hypothesis (property-based testing)  |
| Qualidade    | mypy (strict), black, isort, ruff             |

## Pipeline de análise

```
Entrada (arquivo ou texto)
        ↓
   Parser (Drain3)          → extrai LogEntry + LogTemplate
        ↓
    Analyzer                → detecta spikes, stack traces, distribuição
        ↓
  AIEngine (Ollama)         → gera diagnóstico com hipóteses
        ↓
  Repository (SQLite)       → persiste resultado
        ↓
   Resposta JSON            → estilo Datadog/Sentry
```

## Configuração

Variáveis de ambiente (prefixo `LOGPULSE_`):

```env
LOGPULSE_OLLAMA_BASE_URL=http://localhost:11434/v1
LOGPULSE_OLLAMA_MODEL=llama3
LOGPULSE_OLLAMA_TIMEOUT=30
LOGPULSE_DATABASE_URL=logpulse.db
```

Copie `.env.example` para `.env` e ajuste conforme necessário.

## Testes

```bash
pytest                          # roda todos os testes com cobertura
pytest tests/api/ -v            # testa apenas os endpoints
pytest tests/parsers/ -v        # testa apenas o parser
```

## GitHub Flow

**Branches:**
- `main` → protegida, sempre estável
- `feature/*` → novas funcionalidades
- `bugfix/*` → correções de bugs

**Commits semânticos:**
- `feat:` para novas funcionalidades
- `fix:` para correções
- `docs:` para documentação
- `refactor:` para refatorações

## Status

🚧 Em desenvolvimento ativo
