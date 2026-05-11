# Documento de Requisitos — LogPulse IA (MVP)

## 1. Introdução

O **LogPulse IA** é uma API REST construída com FastAPI que analisa logs brutos (stacktraces, logs de produção) e fornece diagnóstico inteligente com sugestões de causa raiz e ações corretivas. O diagnóstico é gerado por um LLM local via **Ollama + LLaMA 3**, sem dependência de APIs externas pagas.

> **Escopo do MVP:** API REST com FastAPI, IA nativa via Ollama, persistência em SQLite e parsing via Drain3. Integrações com fontes externas fazem parte do roadmap.

### 1.1 Glossário

| Termo            | Definição                                                                        |
|------------------|----------------------------------------------------------------------------------|
| `LogEntry`       | Unidade atômica de log: timestamp, nível, mensagem e metadados                   |
| `LogStream`      | Sequência ordenada de `LogEntry` extraída da entrada do usuário                  |
| `LogTemplate`    | Padrão extraído pelo Drain3 a partir de mensagens similares (ex: `DB timeout *`) |
| `Parser`         | Componente que usa Drain3 para transformar texto bruto em `LogEntry` estruturado |
| `Analyzer`       | Componente que processa um `LogStream` e produz `AnalysisResult`                 |
| `AnalysisResult` | Estrutura com anomalias detectadas, templates e sugestões de investigação        |
| `AIEngine`       | Componente que usa Ollama/LLaMA 3 para gerar diagnóstico a partir do resultado   |
| `SeverityLevel`  | Enumeração: DEBUG, INFO, WARNING, ERROR, CRITICAL                                |
| `MTTR`           | Mean Time To Resolution — tempo médio de resolução de incidentes                 |

---

## 2. Visão Geral do Sistema

### 2.1 Objetivo

Reduzir o MTTR de incidentes em produção permitindo que o usuário envie logs via API e receba um diagnóstico estruturado com causa raiz provável e ações práticas, gerado por IA local.

### 2.2 Pipeline de Dados

```
Entrada (arquivo ou texto)
        ↓
   Parser (Drain3)
        ↓
    LogStream
        ↓
    Analyzer
        ↓
  AnalysisResult
        ↓
  AIEngine (Ollama/LLaMA 3)
        ↓
  Diagnóstico → Persistência (SQLite)
        ↓
   Resposta JSON
```

### 2.3 Endpoints da API

| Método   | Rota                 | Descrição                        |
|----------|----------------------|----------------------------------|
| `POST`   | `api/v1/logs/file`   | Envio de log via arquivo         |
| `POST`   | `api/v1/logs/text`   | Envio de log via texto           |
| `GET`    | `api/v1/logs`        | Listagem paginada de logs        |
| `GET`    | `api/v1/logs/{id}`   | Consulta de um log pelo ID       |
| `DELETE` | `api/v1/logs/{id}`   | Remoção de um log pelo ID        |

### 2.4 Stack do MVP

| Componente   | Tecnologia                                       |
|--------------|--------------------------------------------------|
| API          | FastAPI + Pydantic                               |
| IA           | Ollama + LLaMA 3 (porta 11434) via OpenAI SDK    |
| Parsing      | Drain3                                           |
| Persistência | SQLite                                           |
| Testes       | pytest + hypothesis (cobertura mínima: 30%)      |
| Qualidade    | mypy (strict), black, isort, ruff                |

### 2.5 Fora do Escopo do MVP

- Integração com WildFly, Rancher, Kubernetes
- Suporte a múltiplos provedores de LLM (OpenAI, Gemini, Claude)
- Memória com embeddings
- Monitoramento de logs em tempo real
- Interface web de visualização

---

## 3. Requisitos Funcionais

> Padrão de escrita adotado:
> `WHEN <condição>, THE <componente> SHALL <comportamento>`
> `IF <condição>, THEN THE <componente> SHALL <comportamento>`

---

### RF-01 — Envio de Log via Arquivo

**User Story:** Como engenheiro de operações, quero fazer upload de um arquivo de log pela API, para analisar incidentes sem precisar copiar o conteúdo manualmente.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | WHEN o usuário enviar um arquivo via `POST api/v1/logs/file`, THE API SHALL aceitar arquivos nos formatos `.log` e `.txt`. |
| 2 | IF o arquivo enviado estiver vazio, THEN THE API SHALL retornar HTTP 422 com mensagem descritiva. |
| 3 | IF o arquivo exceder 50 MB, THEN THE API SHALL retornar HTTP 413 com mensagem descritiva. |
| 4 | IF o formato do arquivo não for suportado, THEN THE API SHALL retornar HTTP 415 com a lista de formatos aceitos. |
| 5 | WHEN o arquivo for aceito, THE API SHALL persistir o log no SQLite e retornar o `id` gerado na resposta. |

---

### RF-02 — Envio de Log via Texto

**User Story:** Como desenvolvedor, quero colar um trecho de log diretamente em um campo de texto da API, para analisar rapidamente um erro sem precisar salvar um arquivo.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | WHEN o usuário enviar texto via `POST api/v1/logs/text` com o campo `content` preenchido, THE API SHALL processar o conteúdo como um `LogStream`. |
| 2 | IF o campo `content` estiver vazio ou ausente, THEN THE API SHALL retornar HTTP 422 com mensagem descritiva. |
| 3 | IF o texto enviado exceder 100.000 caracteres, THEN THE API SHALL retornar HTTP 413 com mensagem descritiva. |
| 4 | THE API SHALL aceitar texto com quebras de linha `\n` e `\r\n` sem diferença de comportamento. |
| 5 | WHEN o texto for aceito, THE API SHALL persistir o log no SQLite e retornar o `id` gerado na resposta. |

---

### RF-03 — Parsing e Extração de Templates com Drain3

**User Story:** Como usuário, quero que o sistema detecte automaticamente padrões no log enviado, para não precisar configurar expressões regulares manualmente.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | WHEN o `Parser` receber o conteúdo, THE `Parser` SHALL usar o Drain3 para extrair `LogTemplate` a partir das mensagens do `LogStream`. |
| 2 | THE `Parser` SHALL reconhecer os formatos: JSON estruturado, Syslog RFC 3164 e texto livre genérico. |
| 3 | IF nenhum formato conhecido for detectado, THEN THE `Parser` SHALL tratar cada linha como texto livre com nível INFO. |
| 4 | THE `Parser` SHALL normalizar aliases de severidade: `WARN → WARNING`, `ERR → ERROR`, `FATAL → CRITICAL`, `TRACE → DEBUG`. |
| 5 | WHEN o `timestamp` de uma linha não puder ser determinado, THE `Parser` SHALL usar o momento do processamento e marcar `timestamp_inferred = true`. |
| 6 | WHEN o `level` de uma linha não puder ser determinado, THE `Parser` SHALL atribuir INFO e marcar `level_inferred = true`. |

---

### RF-04 — Detecção de Anomalias

**User Story:** Como engenheiro de operações, quero que o sistema detecte automaticamente anomalias no log enviado, para identificar problemas sem precisar ler cada linha manualmente.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | WHEN o `Analyzer` processar um `LogStream`, THE `Analyzer` SHALL agrupar `LogEntry` com mensagens similares usando os `LogTemplate` gerados pelo Drain3. |
| 2 | WHEN a frequência de ERROR ou CRITICAL exceder 10 ocorrências em uma janela de 60 segundos, THE `Analyzer` SHALL sinalizar um spike no `AnalysisResult`. |
| 3 | WHEN o `Analyzer` identificar stack traces (Python traceback, Java stacktrace, Go panic), THE `Analyzer` SHALL agrupar as linhas relacionadas em um único evento de erro. |
| 4 | THE `Analyzer` SHALL calcular a distribuição de `LogEntry` por `SeverityLevel`. |
| 5 | IF o `LogStream` contiver menos de 2 `LogEntry`, THEN THE `Analyzer` SHALL retornar `AnalysisResult` com `insufficient_data = true`, sem executar detecção de anomalias. |

---

### RF-05 — Diagnóstico com IA (Ollama + LLaMA 3)

**User Story:** Como engenheiro de plantão, quero que o sistema use IA local para sugerir hipóteses de causa raiz, para resolver incidentes mais rapidamente sem depender de serviços externos.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | WHEN a API receber uma requisição de análise, THE `AIEngine` SHALL enviar o `AnalysisResult` ao Ollama (LLaMA 3) via OpenAI SDK apontando para `http://localhost:11434`. |
| 2 | WHEN houver pelo menos um spike ou cluster de erro, THE `AIEngine` SHALL sugerir no mínimo 3 hipóteses de causa raiz ordenadas por probabilidade estimada. |
| 3 | WHEN o `AIEngine` produzir hipóteses, THE `AIEngine` SHALL incluir pelo menos um comando ou ação de investigação por hipótese. |
| 4 | THE `AIEngine` SHALL apontar a linha provável do erro no log quando identificável. |
| 5 | IF o Ollama não estiver disponível na porta 11434, THEN THE API SHALL retornar HTTP 503 com mensagem orientando como iniciar o serviço. |
| 6 | THE `AIEngine` SHALL incluir no diagnóstico apenas informações derivadas do `LogStream` fornecido, sem inventar eventos ou timestamps. |
| 7 | THE `AIEngine` SHALL ter timeout de 30 segundos por chamada ao Ollama, retornando HTTP 504 em caso de estouro. |

---

### RF-06 — Persistência e Consulta de Logs (SQLite)

**User Story:** Como desenvolvedor, quero consultar análises anteriores pelo ID, para revisar diagnósticos sem precisar reenviar o log.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | WHEN uma análise for concluída, THE API SHALL persistir o log original, o `AnalysisResult` e o diagnóstico da IA no SQLite com um `id` único. |
| 2 | WHEN o usuário chamar `GET api/v1/logs/{id}`, THE API SHALL retornar o registro completo correspondente ao `id`. |
| 3 | IF o `id` não existir, THEN THE API SHALL retornar HTTP 404 com mensagem descritiva. |
| 4 | WHEN o usuário chamar `GET api/v1/logs`, THE API SHALL retornar uma lista paginada com os campos `id`, `created_at` e `summary`. |
| 5 | WHEN o usuário chamar `DELETE api/v1/logs/{id}`, THE API SHALL remover o registro do SQLite e retornar HTTP 204. |
| 6 | IF o `id` para deleção não existir, THEN THE API SHALL retornar HTTP 404 com mensagem descritiva. |

---

### RF-07 — Resposta Estruturada da API

**User Story:** Como desenvolvedor integrando o LogPulse IA, quero receber a resposta em JSON estruturado e validado pelo Pydantic, para processar os resultados programaticamente.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | THE API SHALL retornar sempre um JSON com os campos: `id`, `total_entries`, `error_count`, `warning_count`, `spikes`, `anomalies`, `ai_diagnosis`. |
| 2 | THE API SHALL validar todos os payloads de entrada e saída com schemas Pydantic. |
| 3 | THE API SHALL retornar HTTP 200 para análises concluídas com sucesso. |
| 4 | THE API SHALL retornar respostas de erro com o campo `detail` descrevendo o problema de forma clara. |
| 5 | THE API SHALL expor documentação interativa em `/docs` (Swagger UI) e `/redoc`. |

---

### RF-08 — Configuração do Sistema

**User Story:** Como administrador, quero configurar o LogPulse IA via arquivo de configuração para padronizar o comportamento em diferentes ambientes.

| # | Critério de Aceitação |
|---|-----------------------|
| 1 | THE LogPulse IA SHALL carregar configurações de `logpulse.toml` no diretório atual ou em `~/.config/logpulse/logpulse.toml`. |
| 2 | WHEN ambos os arquivos existirem, THE LogPulse IA SHALL mesclar as configurações com precedência para o arquivo local. |
| 3 | THE LogPulse IA SHALL aceitar `LOGPULSE_API_KEY` como variável de ambiente com precedência sobre o arquivo de configuração. |
| 4 | IF o arquivo de configuração contiver TOML inválido, THEN THE LogPulse IA SHALL registrar o erro no log de inicialização e usar a configuração padrão. |

---

## 4. Requisitos Não Funcionais

| ID     | Categoria        | Requisito                                                                                     |
|--------|------------------|-----------------------------------------------------------------------------------------------|
| RNF-01 | Performance      | A API SHALL processar arquivos de até 50 MB sem esgotar memória, via leitura linha a linha.   |
| RNF-02 | Performance      | O parsing de uma linha SHALL ocorrer em menos de 1 ms em hardware convencional.               |
| RNF-03 | Confiabilidade   | Uma linha malformada NÃO SHALL interromper o processamento do `LogStream`.                    |
| RNF-04 | Segurança        | O `AIEngine` SHALL enviar ao LLM apenas o `AnalysisResult` e amostras, nunca o log completo. |
| RNF-05 | Manutenibilidade | O código SHALL passar em `mypy --strict`, `ruff` e `black` sem erros.                        |
| RNF-06 | Testabilidade    | O projeto SHALL manter cobertura mínima de **30%** com `pytest` e `hypothesis`.              |
| RNF-07 | Compatibilidade  | O sistema SHALL suportar Python 3.11+ em Linux, macOS e Windows.                             |
| RNF-08 | Resiliência      | Chamadas ao Ollama SHALL ter timeout de 30 segundos com falha rápida e mensagem descritiva.  |
| RNF-09 | Qualidade        | A resposta do diagnóstico SHALL ser coerente, clara e com qualidade técnica.                 |

---

## 5. Regras de Negócio

| ID    | Regra                                                                                                    |
|-------|----------------------------------------------------------------------------------------------------------|
| RN-01 | Um `LogEntry` é considerado crítico se `level` for ERROR ou CRITICAL.                                   |
| RN-02 | Um spike é definido como 10 ou mais entradas críticas em uma janela deslizante de 60 segundos.          |
| RN-03 | O `AIEngine` é sempre acionado automaticamente após a análise — não é opcional por flag.                |
| RN-04 | A variável de ambiente `LOGPULSE_API_KEY` sempre tem precedência sobre qualquer arquivo de configuração. |
| RN-05 | O Drain3 inspeciona todas as linhas do `LogStream` para construir os `LogTemplate`.                     |
| RN-06 | Aliases de severidade (`WARN`, `ERR`, `FATAL`, `TRACE`) são normalizados antes de qualquer análise.     |
| RN-07 | Análises com menos de 2 `LogEntry` retornam `AnalysisResult` com `insufficient_data = true`.            |
| RN-08 | O tamanho máximo de arquivo aceito é 50 MB. O tamanho máximo de texto colado é 100.000 caracteres.      |
| RN-09 | Todo log analisado é persistido no SQLite com `id`, `created_at`, resultado e diagnóstico.              |

---

## 6. Entradas e Saídas

### 6.1 Entradas

| Endpoint             | Método | Tipo                  | Campos obrigatórios              |
|----------------------|--------|-----------------------|----------------------------------|
| `api/v1/logs/file`   | POST   | `multipart/form-data` | `file` (`.log` ou `.txt`)        |
| `api/v1/logs/text`   | POST   | `application/json`    | `content` (string)               |
| `api/v1/logs`        | GET    | query params          | `page`, `page_size` (opcionais)  |
| `api/v1/logs/{id}`   | GET    | path param            | `id` (UUID)                      |
| `api/v1/logs/{id}`   | DELETE | path param            | `id` (UUID)                      |

### 6.2 Saída — Análise (HTTP 200)

```json
{
  "id": "uuid-gerado",
  "created_at": "2024-01-15T10:00:00Z",
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
      }
    ]
  }
}
```

### 6.3 Respostas de Erro

| HTTP | Situação                                      |
|------|-----------------------------------------------|
| 404  | Log com `id` não encontrado                   |
| 413  | Arquivo ou texto excede o tamanho máximo      |
| 415  | Formato de arquivo não suportado              |
| 422  | Campo obrigatório ausente ou inválido         |
| 503  | Ollama indisponível na porta 11434            |
| 504  | Timeout na chamada ao Ollama (> 30s)          |
| 500  | Erro interno inesperado                       |

---

## 7. Roadmap (Fora do Escopo do MVP)

| Item                                               | Versão prevista |
|----------------------------------------------------|-----------------|
| Integração com WildFly e Rancher                   | v2              |
| Suporte a múltiplos LLMs (OpenAI, Gemini, Claude)  | v2              |
| Memória com embeddings                             | v2              |
| Monitoramento de logs em tempo real                | v2              |
| Interface web de visualização                      | v2              |
| Integração com Kubernetes                          | v3              |
