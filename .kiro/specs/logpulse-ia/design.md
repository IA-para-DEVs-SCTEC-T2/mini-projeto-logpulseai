# Design — LogPulse IA

## 1. Introdução

O **LogPulse IA** é uma API REST que recebe logs brutos (stacktraces, logs de produção), analisa padrões de erro com auxílio de IA local (Ollama/LLaMA 3) e retorna diagnósticos estruturados com causa raiz e sugestões de correção.

Este documento descreve a arquitetura, os componentes, os fluxos de dados, as integrações externas e as decisões técnicas que guiam o desenvolvimento do sistema.

---

## 2. Visão Geral da Arquitetura

O sistema segue uma arquitetura em camadas, organizada em módulos coesos dentro de `src/`. A comunicação externa ocorre exclusivamente via API REST (FastAPI), e o processamento interno é dividido entre parsing, análise e persistência.

```
┌─────────────────────────────────────────────────────────┐
│                        Cliente                          │
│              (Swagger UI / HTTP Client)                 │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│              src/api/v1/logs/                           │
│   POST /file  │  POST /text  │  GET /  │  GET /{id}     │
│               │              │  DELETE /{id}            │
└──────┬────────┴──────┬───────┴─────────────────────────┘
       │               │
┌──────▼───────┐ ┌─────▼────────────────────────────────┐
│   Parsers    │ │           Services Layer              │
│  (Drain3)    │ │   src/services/                       │
│ src/parsers/ │ │   - LogAnalysisService                │
└──────┬───────┘ │   - DiagnosticService                 │
       │         └──────────────┬────────────────────────┘
       └──────────────┬─────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    AI Layer                             │
│                  src/ai/                                │
│         Ollama / LLaMA 3 (porta 11434)                  │
│         via OpenAI Python SDK (drop-in)                 │
└─────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 Persistence Layer                       │
│               src/models/                               │
│           SQLite + Pydantic Schemas                     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Componentes do Sistema

### 3.1 API Layer — `src/api/`

Responsável por expor os endpoints REST e validar os payloads de entrada/saída via Pydantic.

| Módulo                        | Responsabilidade                                      |
|-------------------------------|-------------------------------------------------------|
| `src/api/v1/logs/routes.py`   | Definição das rotas e handlers dos endpoints          |
| `src/api/v1/logs/schemas.py`  | Schemas Pydantic de request e response                |

**Endpoints expostos:**

| Método   | Rota                | Descrição                        |
|----------|---------------------|----------------------------------|
| `POST`   | `api/v1/logs/file`  | Recebe log via upload de arquivo |
| `POST`   | `api/v1/logs/text`  | Recebe log via texto puro        |
| `GET`    | `api/v1/logs`       | Lista logs com paginação         |
| `GET`    | `api/v1/logs/{id}`  | Consulta log por ID              |
| `DELETE` | `api/v1/logs/{id}`  | Remove log por ID                |

---

### 3.2 Services Layer — `src/services/`

Contém a lógica de negócio desacoplada da camada HTTP.

| Módulo                              | Responsabilidade                                              |
|-------------------------------------|---------------------------------------------------------------|
| `src/services/log_analysis.py`      | Coordena parsing, extração de metadados e chamada à IA        |
| `src/services/diagnostic.py`        | Formata o diagnóstico final (causa raiz, sugestão de correção)|

---

### 3.3 Parsers Layer — `src/parsers/`

Responsável por transformar logs brutos em templates estruturados usando a biblioteca **Drain3**.

| Módulo                        | Responsabilidade                                         |
|-------------------------------|----------------------------------------------------------|
| `src/parsers/drain_parser.py` | Wrapper do Drain3 para extração de templates de log      |
| `src/parsers/log_reader.py`   | Leitura e normalização de arquivos `.log` e `.txt`       |

---

### 3.4 AI Layer — `src/ai/`

Integração com o modelo LLaMA 3 via Ollama, utilizando o OpenAI Python SDK como drop-in replacement.

| Módulo                    | Responsabilidade                                              |
|---------------------------|---------------------------------------------------------------|
| `src/ai/ollama_client.py` | Cliente configurado para apontar ao servidor Ollama local     |
| `src/ai/prompts.py`       | Templates de prompt para análise e diagnóstico de logs        |

**Configuração do cliente:**
- Base URL: `http://localhost:11434/v1`
- Modelo: `llama3`
- SDK: `openai` (drop-in replacement)

---

### 3.5 Models Layer — `src/models/`

Define os modelos de persistência (SQLite via SQLAlchemy ou similar) e os schemas Pydantic.

| Módulo                    | Responsabilidade                                    |
|---------------------------|-----------------------------------------------------|
| `src/models/log_entry.py` | Modelo de dados do log armazenado                   |
| `src/models/schemas.py`   | Schemas Pydantic compartilhados entre camadas       |

**Campos principais do modelo `LogEntry`:**

| Campo          | Tipo       | Descrição                              |
|----------------|------------|----------------------------------------|
| `id`           | `str`      | UUID do registro                       |
| `raw_content`  | `str`      | Conteúdo bruto do log                  |
| `template`     | `str`      | Template extraído pelo Drain3          |
| `severity`     | `str`      | Nível de severidade (ERROR, WARN, etc.)|
| `diagnosis`    | `str`      | Diagnóstico gerado pela IA             |
| `suggestion`   | `str`      | Sugestão de correção                   |
| `created_at`   | `datetime` | Timestamp de criação                   |

---

### 3.6 Core Layer — `src/core/`

Configurações globais, dependências e utilitários transversais.

| Módulo                   | Responsabilidade                                         |
|--------------------------|----------------------------------------------------------|
| `src/core/config.py`     | Leitura de configurações via `tomllib` (`pyproject.toml`)|
| `src/core/database.py`   | Inicialização e sessão do banco SQLite                   |
| `src/core/dependencies.py` | Injeção de dependências FastAPI                        |

---

## 4. Fluxos de Dados

### 4.1 Fluxo: Envio de Log via Arquivo (`POST /api/v1/logs/file`)

```
Cliente
  │
  ├─► [1] Upload do arquivo (.log / .txt)
  │
  ▼
API Layer (routes.py)
  │
  ├─► [2] Validação do tipo e tamanho do arquivo (Pydantic)
  │
  ▼
Parsers Layer (log_reader.py)
  │
  ├─► [3] Leitura e normalização do conteúdo
  │
  ▼
Parsers Layer (drain_parser.py)
  │
  ├─► [4] Extração de template via Drain3
  │
  ▼
Services Layer (log_analysis.py)
  │
  ├─► [5] Montagem do prompt com template + log bruto
  │
  ▼
AI Layer (ollama_client.py)
  │
  ├─► [6] Chamada ao LLaMA 3 via Ollama (localhost:11434)
  │
  ▼
Services Layer (diagnostic.py)
  │
  ├─► [7] Estruturação do diagnóstico (causa raiz + sugestão)
  │
  ▼
Models Layer (log_entry.py)
  │
  ├─► [8] Persistência no SQLite
  │
  ▼
API Layer (routes.py)
  │
  └─► [9] Retorno do JSON estruturado ao cliente
```

### 4.2 Fluxo: Envio de Log via Texto (`POST /api/v1/logs/text`)

Idêntico ao fluxo de arquivo, com a diferença de que o passo [3] recebe o texto diretamente do payload JSON, sem leitura de arquivo.

### 4.3 Fluxo: Consulta de Log (`GET /api/v1/logs/{id}`)

```
Cliente ──► API Layer ──► Models Layer (SQLite) ──► Retorno JSON
```

### 4.4 Fluxo: Listagem Paginada (`GET /api/v1/logs`)

```
Cliente ──► API Layer ──► Models Layer (SQLite, paginado) ──► Retorno JSON
```

### 4.5 Fluxo: Remoção de Log (`DELETE /api/v1/logs/{id}`)

```
Cliente ──► API Layer ──► Models Layer (SQLite, delete) ──► 204 No Content
```

---

## 5. Integrações Externas

### 5.1 Ollama / LLaMA 3

| Atributo       | Valor                          |
|----------------|--------------------------------|
| Tipo           | LLM local                      |
| Modelo         | `llama3`                       |
| Protocolo      | HTTP (compatível OpenAI)       |
| Endereço       | `http://localhost:11434/v1`    |
| SDK            | `openai` (drop-in replacement) |
| Pré-requisito  | Ollama instalado e em execução |

### 5.2 Drain3

| Atributo  | Valor                                          |
|-----------|------------------------------------------------|
| Tipo      | Biblioteca Python de parsing de logs           |
| Função    | Extração de templates a partir de logs brutos  |
| Instalação| `pip install drain3`                           |

---

## 6. Decisões Técnicas (ADR Simplificado)

### ADR-001 — FastAPI como framework web

**Contexto:** Necessidade de uma API REST com documentação automática (Swagger) e validação de schemas.

**Decisão:** Usar FastAPI.

**Justificativa:** Suporte nativo a Pydantic, geração automática de OpenAPI/Swagger, alta performance assíncrona e tipagem estática compatível com `mypy`.

---

### ADR-002 — SQLite como banco de dados

**Contexto:** Execução local sem dependência de infraestrutura externa.

**Decisão:** Usar SQLite.

**Justificativa:** Zero configuração, embutido no Python, suficiente para o volume de dados esperado em ambiente local/desenvolvimento.

---

### ADR-003 — OpenAI SDK como cliente do Ollama

**Contexto:** Ollama expõe uma API compatível com o formato OpenAI.

**Decisão:** Usar o `openai` Python SDK apontando para `localhost:11434`.

**Justificativa:** Permite trocar o provedor de LLM (OpenAI, Gemini, Claude) no futuro apenas alterando a configuração, sem mudar o código de integração.

---

### ADR-004 — Drain3 para parsing de logs

**Contexto:** Logs brutos possuem alta variabilidade (IDs, timestamps, valores dinâmicos) que dificultam análise direta.

**Decisão:** Usar Drain3 para extrair templates estáveis.

**Justificativa:** Reduz o ruído enviado ao LLM, melhora a qualidade do diagnóstico e permite agrupar logs similares.

---

### ADR-005 — Tipagem estática com mypy (strict)

**Contexto:** Projeto Python com múltiplas camadas e integrações.

**Decisão:** Usar `mypy` em modo strict.

**Justificativa:** Detecta erros em tempo de desenvolvimento, melhora a manutenibilidade e documenta contratos de interface implicitamente.

---

## 7. Estrutura de Pastas (Referência)

```
src/
├── api/
│   └── v1/
│       └── logs/
│           ├── routes.py       # Handlers dos endpoints
│           └── schemas.py      # Schemas Pydantic de I/O
├── services/
│   ├── log_analysis.py         # Orquestração da análise
│   └── diagnostic.py           # Formatação do diagnóstico
├── parsers/
│   ├── drain_parser.py         # Wrapper Drain3
│   └── log_reader.py           # Leitura de arquivos
├── ai/
│   ├── ollama_client.py        # Cliente OpenAI SDK → Ollama
│   └── prompts.py              # Templates de prompt
├── models/
│   ├── log_entry.py            # Modelo SQLite
│   └── schemas.py              # Schemas compartilhados
└── core/
    ├── config.py               # Configurações (tomllib)
    ├── database.py             # Sessão SQLite
    └── dependencies.py         # Injeção de dependências FastAPI
```

---

## 8. Considerações Futuras

- Suporte a múltiplos provedores de LLM (OpenAI, Gemini, Claude) via configuração
- Integração com fontes externas de logs (WildFly, Rancher)
- Implementação de memória semântica com embeddings
- Monitoramento de logs em tempo real (WebSocket ou SSE)
- Interface web para visualização dos diagnósticos
