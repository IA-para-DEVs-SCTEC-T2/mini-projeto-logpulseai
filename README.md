# LogPulse IA

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![Status](https://img.shields.io/badge/status-MVP%20em%20desenvolvimento-yellow)
![Testes](https://img.shields.io/badge/cobertura%20mínima-30%25-green)
![Licença](https://img.shields.io/badge/licença-MIT-lightgrey)

> Envie seus logs, receba o diagnóstico. IA local, sem custo de API.

**LogPulse IA** é uma API REST que analisa logs brutos — stacktraces, logs de produção, arquivos `.log` e `.txt` — e retorna um diagnóstico inteligente com causa raiz provável e ações corretivas, gerado por um LLM local via **Ollama + LLaMA 3**.

Feito para engenheiros e times de operações que precisam investigar incidentes rapidamente, sem depender de serviços externos pagos.

---

## Sumário

- [O que faz](#o-que-faz)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Executando localmente](#executando-localmente)
- [Uso da API](#uso-da-api)
- [Configuração](#configuração)
- [Arquitetura](#arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Tecnologias](#tecnologias)
- [Contribuindo](#contribuindo)
- [GitHub Flow](#github-flow)
- [Status](#status)

---

## O que faz

1. Você envia um arquivo de log ou cola um trecho de texto via API
2. O sistema parseia e normaliza as entradas com **Drain3** (detecta padrões automaticamente)
3. O **Analyzer** identifica anomalias: spikes de erro, stack traces agrupados, distribuição por severidade
4. O **AIEngine** envia o resultado ao **Ollama (LLaMA 3)** e retorna hipóteses de causa raiz com ações práticas
5. Tudo é persistido no **SQLite** e consultável por ID

```
Entrada (arquivo ou texto)
        ↓
   Parser (Drain3)          ← detecta JSON, Syslog, texto livre
        ↓
    LogStream
        ↓
    Analyzer                ← spikes, stack traces, distribuição
        ↓
  AnalysisResult
        ↓
  AIEngine (Ollama/LLaMA 3) ← hipóteses + ações
        ↓
  Diagnóstico → SQLite
        ↓
   Resposta JSON
```

---

## Pré-requisitos

| Requisito | Versão mínima | Como verificar |
|-----------|--------------|----------------|
| Python | 3.11+ | `python --version` |
| pip | 23+ | `pip --version` |
| Ollama | qualquer | `ollama --version` |
| LLaMA 3 (modelo) | — | `ollama list` |

### Instalando o Ollama e o modelo LLaMA 3

```bash
# 1. Instale o Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Windows: baixe o instalador em https://ollama.com/download

# 2. Baixe o modelo LLaMA 3
ollama pull llama3

# 3. Inicie o servidor Ollama (porta padrão: 11434)
ollama serve
```

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-logpulseai.git
cd mini-projeto-logpulseai

# 2. Crie e ative um ambiente virtual
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# 3. Instale as dependências
pip install -e ".[dev]"
```

---

## Executando localmente

```bash
# Certifique-se de que o Ollama está rodando
ollama serve

# Inicie a API
uvicorn src.main:app --reload --port 8000
```

A API estará disponível em:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Uso da API

### Enviar log via arquivo

```bash
curl -X POST http://localhost:8000/api/v1/logs/file \
  -F "file=@app.log"
```

### Enviar log via texto

```bash
curl -X POST http://localhost:8000/api/v1/logs/text \
  -H "Content-Type: application/json" \
  -d '{
    "content": "2024-01-15 10:00:01 ERROR Database connection timeout\n2024-01-15 10:00:02 ERROR Database connection timeout"
  }'
```

### Resposta esperada (HTTP 200)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2024-01-15T10:00:05Z",
  "total_entries": 120,
  "error_count": 15,
  "warning_count": 8,
  "insufficient_data": false,
  "spikes": [
    "Spike de 12 erros entre 2024-01-15T10:00:00Z e 2024-01-15T10:01:00Z"
  ],
  "anomalies": [
    "Template repetido 10x: Database connection timeout <*>"
  ],
  "ai_diagnosis": {
    "summary": "Falha recorrente de conexão com banco de dados.",
    "probable_cause": "Pool de conexões esgotado ou banco indisponível.",
    "hypotheses": [
      {
        "description": "Pool de conexões esgotado",
        "probability": "alta",
        "action": "Verificar configuração de max_connections e métricas do pool."
      },
      {
        "description": "Banco de dados indisponível",
        "probability": "média",
        "action": "Checar status do serviço: systemctl status postgresql"
      },
      {
        "description": "Timeout de rede entre app e banco",
        "probability": "baixa",
        "action": "Verificar latência: ping <db-host> e revisar firewall."
      }
    ]
  }
}
```

### Consultar análise por ID

```bash
curl http://localhost:8000/api/v1/logs/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

### Listar análises (paginado)

```bash
curl "http://localhost:8000/api/v1/logs?page=1&page_size=10"
```

### Remover análise

```bash
curl -X DELETE http://localhost:8000/api/v1/logs/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

### Endpoints disponíveis

| Método | Rota | Descrição | Limites |
|--------|------|-----------|---------|
| `POST` | `api/v1/logs/file` | Upload de arquivo de log | Máx. 50 MB, `.log` e `.txt` |
| `POST` | `api/v1/logs/text` | Envio de log como texto | Máx. 100.000 caracteres |
| `GET` | `api/v1/logs` | Listagem paginada | `page` e `page_size` opcionais |
| `GET` | `api/v1/logs/{id}` | Consulta por ID | — |
| `DELETE` | `api/v1/logs/{id}` | Remoção por ID | Retorna HTTP 204 |

### Códigos de resposta

| HTTP | Situação |
|------|----------|
| `200` | Análise concluída com sucesso |
| `204` | Log removido com sucesso |
| `404` | Log com `id` não encontrado |
| `413` | Arquivo ou texto excede o tamanho máximo |
| `415` | Formato de arquivo não suportado |
| `422` | Campo obrigatório ausente ou inválido |
| `503` | Ollama indisponível na porta 11434 |
| `504` | Timeout na chamada ao Ollama (> 30s) |

---

## Configuração

Crie um arquivo `logpulse.toml` na raiz do projeto (ou em `~/.config/logpulse/logpulse.toml` para configuração global):

```toml
[ai]
model = "llama3"
endpoint = "http://localhost:11434"
temperature = 0.7
max_tokens = 1000
timeout_seconds = 30

[parser]
format = "auto"  # auto | json | plaintext | syslog

[analyzer]
spike_threshold = 10   # erros por janela para detectar spike
window_seconds = 60    # tamanho da janela em segundos
min_cluster_size = 3   # mínimo de mensagens para formar cluster

[output]
format = "text"  # text | json
color = true
```

### Precedência de configuração

```
Variáveis de ambiente  >  logpulse.toml local  >  ~/.config/logpulse/logpulse.toml  >  defaults
```

| Variável de ambiente | Efeito |
|----------------------|--------|
| `LOGPULSE_API_KEY` | Chave de API (para uso futuro com OpenAI) |
| `LOGPULSE_MODEL` | Sobrescreve `ai.model` do arquivo de configuração |
| `LOGPULSE_ENDPOINT` | Sobrescreve `ai.endpoint` do arquivo de configuração |

---

## Arquitetura

O sistema segue **arquitetura em camadas** com inversão de dependências:

```
┌──────────────────────────────────────────┐
│              API Layer                   │
│         FastAPI + Pydantic               │
└─────────────────┬────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│           Application Layer              │
│        Analyzer  +  AIEngine             │
└─────────────────┬────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│             Domain Layer                 │
│     LogEntry, AnalysisResult, schemas    │
└─────────────────┬────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│          Infrastructure Layer            │
│       Parsers (Drain3) + Repository      │
│              (SQLite)                    │
└──────────────────────────────────────────┘
```

Cada camada depende apenas de abstrações (Protocols/ABCs) da camada abaixo, nunca de implementações concretas.

---

## Estrutura do projeto

```
mini-projeto-logpulseai/
├── src/                        # Código-fonte principal
│   ├── ai/                     # AIEngine: integração com Ollama via OpenAI SDK
│   │   ├── base.py             # Interface abstrata AIEngine
│   │   └── ollama_engine.py    # Implementação com retry, timeout e validação
│   ├── analyzer/               # Detecção de anomalias e spikes
│   │   ├── base.py             # Interface abstrata LogAnalyzer
│   │   └── detector.py         # AnomalyDetector: spikes, stack traces, distribuição
│   ├── models/                 # Schemas Pydantic (entrada, saída, domínio)
│   │   └── schemas.py          # LogEntry, AnalysisResult, AIDiagnosis, etc.
│   ├── parsers/                # Parsing de logs com Drain3
│   │   ├── base.py             # Interface abstrata LogParser
│   │   ├── drain3_parser.py    # Suporte a JSON, Syslog e texto livre
│   │   └── normalizer.py       # Normalização de severidade e timestamps
│   ├── repository/             # Persistência SQLite
│   │   ├── base.py             # Interface abstrata LogRepository
│   │   └── sqlite_repository.py # CRUD assíncrono com aiosqlite
│   └── exceptions.py           # Hierarquia de exceções do projeto
├── tests/                      # Testes automatizados (espelha src/)
│   ├── ai/
│   ├── analyzer/
│   ├── models/
│   ├── parsers/
│   └── repository/
├── logs/                       # Arquivos .log e .txt de exemplo para testes
├── docs/                       # Documentação técnica adicional
│   └── prompts/                # Registro de prompts utilizados no desenvolvimento
├── .github/
│   └── workflows/              # CI: validação de branch, commit, cobertura
├── logpulse.toml               # Configuração do projeto (exemplo)
├── pyproject.toml              # Dependências e configuração de ferramentas
└── README.md
```

---

## Tecnologias

| Tecnologia | Papel no projeto |
|------------|-----------------|
| **Python 3.11+** | Linguagem principal — ecossistema maduro para IA e parsing |
| **FastAPI** | Framework da API REST com validação automática e Swagger integrado |
| **Pydantic v2** | Validação de schemas de entrada e saída da API |
| **Ollama + LLaMA 3** | LLM local para diagnóstico — sem custo de API externa |
| **OpenAI SDK** | Cliente HTTP usado como drop-in replacement apontando para o Ollama |
| **Drain3** | Extração de templates de log por agrupamento de mensagens similares |
| **SQLite + aiosqlite** | Persistência leve e assíncrona dos logs e diagnósticos |
| **pytest** | Framework de testes com fixtures e parametrização |
| **hypothesis** | Property-based testing para validar invariantes dos parsers |
| **pytest-cov** | Relatório de cobertura de código integrado ao pytest |
| **mypy** | Verificação de tipos estática em modo strict |
| **black** | Formatação automática de código (line length: 100) |
| **isort** | Ordenação automática de imports |
| **ruff** | Linter rápido (substitui flake8, pylint, pyupgrade) |
| **tomllib** | Parser TOML nativo (stdlib Python 3.11+) para `logpulse.toml` |

---

## Contribuindo

### 1. Configure o ambiente

```bash
git clone https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-logpulseai.git
cd mini-projeto-logpulseai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Crie sua branch a partir da `main`

```bash
# Nova funcionalidade
git checkout -b feature/minha-funcionalidade

# Correção de bug
git checkout -b bugfix/descricao-do-bug
```

### 3. Desenvolva e faça commits semânticos

```bash
git commit -m "feat: adiciona endpoint de upload de arquivo"
git commit -m "fix: corrige parsing de stacktrace Java"
git commit -m "docs: atualiza README com exemplos de uso"
git commit -m "refactor: simplifica lógica do analyzer"
```

> ⚠️ Apenas os tipos `feat`, `fix`, `docs` e `refactor` são aceitos pelo CI.

### 4. Rode os testes antes de abrir o PR

```bash
# Todos os testes com cobertura
pytest

# Apenas um módulo específico
pytest tests/parsers/ -v

# Com relatório HTML de cobertura
pytest --cov=src --cov-report=html
```

### 5. Valide os padrões do projeto

```bash
# Tipagem estática
mypy --strict src/

# Formatação
black --check src/ tests/
isort --check src/ tests/

# Linting
ruff check src/ tests/

# Aplicar formatação automaticamente
black src/ tests/
isort src/ tests/
```

### 6. Abra o Pull Request

```bash
gh pr create \
  --title "feat: adiciona endpoint de upload de arquivo" \
  --body "Implementa POST api/v1/logs/file com validação Pydantic e persistência SQLite." \
  --base main
```

---

## GitHub Flow

### Regras de branch (validadas automaticamente pelo CI)

| Padrão | Quando usar |
|--------|-------------|
| `feature/<nome>` | Nova funcionalidade |
| `bugfix/<nome>` | Correção de bug |

Regras do `<nome>`: letras minúsculas, números e hífens, mínimo 3 caracteres.

```bash
✅ feature/endpoint-logs-file
✅ bugfix/correcao-timeout-ollama

❌ minha-feature          # sem prefixo
❌ feature/ab             # nome muito curto
❌ hotfix/bug-critico     # prefixo não permitido
```

### Validações automáticas no CI

Ao abrir ou atualizar um PR, o GitHub Actions verifica:

| Check | O que valida |
|-------|-------------|
| `branch-validation` | Nome da branch segue o padrão `feature/*` ou `bugfix/*` |
| `commit-validation` | Todos os commits usam `feat`, `fix`, `docs` ou `refactor` |
| `branch-up-to-date` | Branch está atualizada com `main` |
| `approval-gate` | PR tem pelo menos 1 aprovação de outro colaborador |
| `pytest + cobertura` | Testes passando e cobertura ≥ 30% |
| `mypy + ruff + black` | Tipagem e formatação sem erros |

### Fluxo completo

```
1. git checkout -b feature/<nome>     # cria branch a partir de main
2. # desenvolve e commita
3. git push -u origin feature/<nome>  # publica a branch
4. gh pr create --base main           # abre o PR
5. # aguarda 1 aprovação de outro colaborador
6. # merge na main após aprovação e CI verde
```

> ⚠️ Nunca faça commit direto na `main`. Nunca aprove seu próprio PR.

---

## Status

**MVP em desenvolvimento ativo**

| Módulo | Status |
|--------|--------|
| Modelos Pydantic (`src/models/`) | ✅ Implementado |
| Parser com Drain3 (`src/parsers/`) | ✅ Implementado |
| Analyzer de anomalias (`src/analyzer/`) | ✅ Implementado |
| AIEngine com Ollama (`src/ai/`) | ✅ Implementado |
| Repositório SQLite (`src/repository/`) | ✅ Implementado |
| API FastAPI (`src/api/`) | 🚧 Em desenvolvimento |
| Configuração TOML (`src/config.py`) | 🚧 Em desenvolvimento |
| Testes de integração | 🚧 Em desenvolvimento |

### Roadmap (v2+)

- Integração com WildFly, Rancher e Kubernetes
- Suporte a múltiplos LLMs (OpenAI, Gemini, Claude)
- Memória com embeddings para contexto histórico
- Monitoramento de logs em tempo real
- Interface web de visualização dos diagnósticos
