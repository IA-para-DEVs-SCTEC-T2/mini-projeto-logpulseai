# LogPulse IA

> Analise logs de produção e receba diagnóstico inteligente com causa raiz e ações corretivas.

## Objetivo

O **LogPulse IA** é uma API REST construída com FastAPI que recebe logs brutos (stacktraces, logs de produção), detecta anomalias automaticamente e gera diagnóstico inteligente via IA local (Ollama + LLaMA 3), sem dependência de APIs externas pagas.

## Como rodar

**Pré-requisitos:** Python 3.11+, pip, [Ollama](https://ollama.com) instalado e rodando com o modelo `llama3.2:3b`.

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

## Entendendo a resposta da API

### 📦 Paginação (`GET /api/v1/logs`)

| Campo       | Descrição                              |
|-------------|----------------------------------------|
| `items`     | Análises retornadas nesta página       |
| `total`     | Total de registros no banco            |
| `page`      | Página atual                           |
| `page_size` | Itens por página                       |
| `pages`     | Total de páginas                       |

---

### 🔍 Identificação da análise

| Campo         | Descrição                                          |
|---------------|----------------------------------------------------|
| `id`          | Identificador único (UUID) da análise              |
| `analyzed_at` | Data e hora em que o log foi processado            |

---

### 📊 `metrics` — contadores do lote analisado

| Campo        | Descrição                                      |
|--------------|------------------------------------------------|
| `total_logs` | Total de linhas de log processadas             |
| `errors`     | Linhas com severidade `ERROR`                  |
| `criticals`  | Linhas com severidade `CRITICAL`               |

---

### 🚨 `issues` — problemas identificados

Cada issue representa um tipo de problema detectado e agrupado por padrão (estilo Sentry):

| Campo            | Descrição                                              |
|------------------|--------------------------------------------------------|
| `title`          | Descrição curta do problema                            |
| `severity`       | Gravidade: `high`, `medium` ou `low`                   |
| `occurrences`    | Quantas vezes esse problema apareceu                   |
| `first_seen`     | Primeira ocorrência nos logs                           |
| `last_seen`      | Última ocorrência nos logs                             |
| `recommendation` | Ação sugerida para resolver                            |
| `affected_class` | Classe/método onde o erro ocorreu (quando identificável) |

---

### ✅ `recommended_actions`

Lista consolidada de ações em ordem de prioridade, gerada a partir dos issues de alta severidade e das hipóteses da IA.

---

### 🎯 `confidence` — confiança do diagnóstico

Valor de `0.0` a `1.0` que indica o quanto a IA confia no diagnóstico gerado:

| Faixa         | Interpretação                                              |
|---------------|------------------------------------------------------------|
| `0.0 – 0.4`   | Baixa confiança — poucos dados ou padrão muito difuso      |
| `0.4 – 0.7`   | Confiança moderada — padrões identificados com alguma ambiguidade |
| `0.7 – 1.0`   | Alta confiança — padrão claro com evidências consistentes  |

> Ex: `0.65` = moderada — padrões identificados, mas com alguma ambiguidade.
> Quando o Ollama está indisponível, o sistema usa diagnóstico heurístico com `confidence` entre `0.3` e `0.7`.

---

> **Resumo rápido:**
> - `metrics` → o que **TEM** nos logs
> - `issues` → o que está **ERRADO**
> - `confidence` → o quanto a IA **CONFIA** no diagnóstico

---

## Estrutura do Projeto

```
logpulse-ia/
├── src/
│   ├── api/              # Camada HTTP (FastAPI, routers, middleware)
│   │   └── v1/
│   │       ├── controllers/  # Controller MVC: valida entrada e delega
│   │       └── routes/       # View MVC: define rotas HTTP
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
| IA           | Ollama + LLaMA 3.2 (3B) via OpenAI SDK (drop-in)  |
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
LOGPULSE_OLLAMA_MODEL=llama3.2:3b
LOGPULSE_OLLAMA_TIMEOUT=120
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
