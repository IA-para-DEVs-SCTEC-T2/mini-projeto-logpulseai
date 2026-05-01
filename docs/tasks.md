# Tasks — LogPulse IA

> Backlog de implementação organizado por módulo, seguindo a arquitetura em camadas:
> `LogSource → Parser → LogEntry → Analyzer → AnalysisResult → AI_Engine → Diagnóstico`

---

## 0. Infraestrutura e Setup

- [ ] Criar `pyproject.toml` com dependências (`typer`, `pyparsing`, `orjson`, `langchain`, `openai`, `watchdog`, `pytest`, `hypothesis`, `mypy`, `black`, `isort`, `ruff`)
- [ ] Configurar `mypy` em modo strict no `pyproject.toml`
- [ ] Configurar `black`, `isort` e `ruff` no `pyproject.toml`
- [ ] Criar `logpulse.toml` de exemplo na raiz do projeto
- [ ] Criar estrutura de pastas em `src/`: `sources/`, `parsers/`, `analyzer/`, `ai/`, `cli/`
- [ ] Criar `src/__init__.py` e `__init__.py` em cada submódulo
- [ ] Espelhar estrutura de `src/` em `tests/` com arquivos `__init__.py`
- [ ] Criar `logs/` com arquivos `.log` de exemplo para testes (JSON, plaintext, syslog, Apache/Nginx)

---

## 1. Modelo de Dados Central (`src/`)

- [ ] Definir enum `SeverityLevel` com valores `DEBUG | INFO | WARNING | ERROR | CRITICAL`
- [ ] Implementar dataclass `LogEntry` com todos os campos especificados:
  - `timestamp: datetime` (sempre com timezone)
  - `level: SeverityLevel`
  - `message: str` (não vazia)
  - `source: str`
  - `raw: str | None`
  - `timestamp_inferred: bool`
  - `level_inferred: bool`
  - `extra: dict`
- [ ] Escrever testes unitários para `LogEntry` (validações de campo, valores padrão)

---

## 2. Sources — Adaptadores de Leitura (`src/sources/`)

- [ ] Definir protocolo/interface `LogSource` (ABC ou `Protocol`)
- [ ] Implementar `FileSource`: leitura de arquivos `.log` e `.txt`
- [ ] Implementar `GzipSource`: leitura de arquivos `.gz` com descompressão em memória
- [ ] Implementar `StdinSource`: leitura via stdin/pipe (`logpulse analyze -`)
- [ ] Implementar detecção automática de fonte com base na extensão/argumento
- [ ] Escrever testes para cada adaptador em `tests/sources/`

---

## 3. Parsers — Transformação de Texto em `LogEntry` (`src/parsers/`)

- [ ] Definir interface `BaseParser` com método `parse(line: str) -> LogEntry`
- [ ] Implementar `JsonParser`: parsing de logs JSON estruturado com `orjson`
- [ ] Implementar `PlaintextParser`: parsing de logs em formato livre com `re`
- [ ] Implementar `SyslogParser`: parsing do formato Syslog (RFC 3164 / RFC 5424)
- [ ] Implementar `ApacheNginxParser`: parsing de logs de acesso Apache/Nginx com `pyparsing`
- [ ] Implementar `AutoParser`: detecção automática de formato e delegação ao parser correto
- [ ] Tratar inferência de `timestamp` e `level` quando ausentes (setar flags `_inferred`)
- [ ] Escrever testes unitários e property-based tests (`hypothesis`) para cada parser em `tests/parsers/`

---

## 4. Analyzer — Detecção de Anomalias (`src/analyzer/`)

- [ ] Definir dataclass `AnalysisResult` com campos: `anomalies`, `spikes`, `patterns`, `summary`
- [ ] Implementar detecção de spikes de erros por janela de tempo
- [ ] Implementar agrupamento de mensagens por padrão (clustering de mensagens similares)
- [ ] Implementar detecção de anomalias: sequências incomuns, ausência de heartbeat, etc.
- [ ] Implementar geração de `summary` textual dos resultados
- [ ] Expor função principal `analyze(entries: list[LogEntry]) -> AnalysisResult`
- [ ] Escrever testes unitários e property-based tests em `tests/analyzer/`

---

## 5. AI Engine — Integração com LLMs (`src/ai/`)

- [ ] Definir interface `AIEngine` com método `diagnose(result: AnalysisResult) -> str`
- [ ] Implementar `OpenAIEngine`: integração com API OpenAI via `langchain` + `openai`
- [ ] Implementar `OllamaEngine`: integração com LLM local via Ollama (endpoint configurável)
- [ ] Implementar prompt de diagnóstico: hipóteses de causa raiz e sugestões de ação
- [ ] Implementar leitura de `LOGPULSE_API_KEY` do ambiente (precedência sobre `logpulse.toml`)
- [ ] Implementar fallback gracioso quando IA não está disponível (modo sem `--ai`)
- [ ] Escrever testes com mocks para `OpenAIEngine` e `OllamaEngine` em `tests/ai/`

---

## 6. Configuração (`src/` ou módulo dedicado)

- [ ] Implementar carregamento de `logpulse.toml` com `tomllib` (stdlib Python 3.11+)
- [ ] Suportar busca em cascata: diretório atual → `~/.config/logpulse/logpulse.toml`
- [ ] Suportar seções `[ai]` (model, endpoint) e `[parser]` (format)
- [ ] Implementar override via variável de ambiente `LOGPULSE_API_KEY`
- [ ] Escrever testes de carregamento e precedência de configuração

---

## 7. CLI — Interface de Linha de Comando (`src/cli/`)

- [ ] Configurar entrypoint com `typer` (ou `click`)
- [ ] Implementar comando `logpulse analyze <fonte>` (análise básica)
- [ ] Implementar flag `--ai`: ativa diagnóstico via AI Engine
- [ ] Implementar flag `--follow`: monitoramento contínuo com `watchdog` (equivalente a `tail -f`)
- [ ] Implementar flag `--output json`: saída estruturada em JSON
- [ ] Implementar `logpulse --help` com documentação de uso
- [ ] Implementar códigos de saída corretos:
  - `0` — análise concluída sem erros
  - `1` — erro de entrada ou configuração
  - `2` — anomalias críticas detectadas
- [ ] Escrever testes de integração da CLI em `tests/cli/`

---

## 8. Monitoramento Contínuo (`src/sources/` + `src/cli/`)

- [ ] Integrar `watchdog` para monitorar alterações em arquivo de log
- [ ] Processar novas linhas incrementalmente no modo `--follow`
- [ ] Garantir encerramento limpo com `Ctrl+C` (tratamento de `KeyboardInterrupt`)

---

## 9. Qualidade de Código e CI

- [ ] Configurar pipeline de CI (GitHub Actions) com: lint (`ruff`), type check (`mypy`), testes (`pytest`)
- [ ] Garantir 100% de cobertura de tipos (mypy strict) em todos os módulos
- [ ] Adicionar `pre-commit` hooks para `black`, `isort`, `ruff` e validação de commits semânticos
- [ ] Garantir que todos os docstrings públicos estejam em português

---

## 10. Documentação

- [ ] Atualizar `README.md` com instruções de instalação (`pip install logpulse-ia`)
- [ ] Documentar todos os formatos de log suportados em `docs/`
- [ ] Documentar configuração do `logpulse.toml` com exemplos em `docs/`
- [ ] Documentar integração com Ollama (LLM local) em `docs/`
- [ ] Criar `CHANGELOG.md` seguindo o padrão Conventional Commits

---

## Ordem de Implementação Sugerida

```
0. Setup → 1. Modelo de Dados → 2. Sources → 3. Parsers
→ 4. Analyzer → 6. Configuração → 7. CLI (básico)
→ 5. AI Engine → 7. CLI (--ai, --follow) → 8. Monitoramento
→ 9. CI/Qualidade → 10. Documentação
```
