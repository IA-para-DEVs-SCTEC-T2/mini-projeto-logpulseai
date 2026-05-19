# Issues para o Board do GitHub

Copie cada bloco abaixo para criar as issues no GitHub Projects.

---

## Issue #1 — 🐛 Corrigir exceções faltantes

**Título:** `fix: adicionar exceções faltantes em src/exceptions.py`  
**Label:** `bug`  
**Branch:** `bugfix/correcao-excecoes-faltantes`  
**Commit:** `fix: adiciona exceções faltantes ao módulo de exceptions`

**Descrição:**  
O arquivo `src/exceptions.py` define apenas 6 exceções, mas o código referencia 7 adicionais que não existem: `AIEngineTimeoutError`, `AIEngineUnavailableError`, `ParsingError`, `StorageError`, `AnalysisError`, `NotFoundError`, `ValidationError`. Isso causa `ImportError` em cascata que impede qualquer módulo de carregar.

**Checklist:**
- [ ] Adicionar `AIEngineTimeoutError(AIEngineError)`
- [ ] Adicionar `AIEngineUnavailableError(AIEngineError)`
- [ ] Adicionar `ParsingError(LogPulseError)`
- [ ] Adicionar `StorageError(LogPulseError)`
- [ ] Adicionar `AnalysisError(LogPulseError)`
- [ ] Adicionar `NotFoundError(LogPulseError)`
- [ ] Adicionar `ValidationError(LogPulseError)`
- [ ] Verificar que `pytest` coleta todos os testes sem ImportError

---

## Issue #2 — 🐛 Adicionar dependências faltantes ao pyproject.toml

**Título:** `fix: adicionar dependências faltantes ao pyproject.toml`  
**Label:** `bug`  
**Branch:** `bugfix/dependencias-pyproject`  
**Commit:** `fix: adiciona pydantic-settings, aiosqlite e structlog ao pyproject.toml`

**Descrição:**  
Três pacotes são usados no código mas não declarados nas dependências: `pydantic-settings`, `aiosqlite`, `structlog`. Um `pip install` limpo falha.

**Checklist:**
- [ ] Adicionar `pydantic-settings~=2.0`
- [ ] Adicionar `aiosqlite~=0.20.0`
- [ ] Adicionar `structlog~=24.1.0`
- [ ] Testar `pip install -e .` em ambiente limpo

---

## Issue #3 — 🐛 Unificar ponto de entrada da aplicação

**Título:** `fix: unificar ponto de entrada FastAPI`  
**Label:** `bug`  
**Branch:** `bugfix/unificar-entrypoint`  
**Commit:** `fix: remove main.py duplicado e unifica entrypoint em api/app.py`

**Descrição:**  
Existem dois arquivos criando instâncias FastAPI: `src/main.py` (routers comentados) e `src/api/app.py` (routers registrados). O `main.py` deve ser removido ou transformado em um simples wrapper que importa o app de `src/api/app.py`.

**Checklist:**
- [ ] Remover `src/main.py` ou transformar em wrapper
- [ ] Garantir que `uvicorn src.api.app:app` funciona
- [ ] Atualizar README com comando correto

---

## Issue #4 — 🐛 Limpar imports duplicados

**Título:** `fix: remover imports duplicados em schemas.py`  
**Label:** `bug`  
**Branch:** `bugfix/imports-duplicados`  
**Commit:** `fix: remove imports duplicados em models/schemas.py`

**Descrição:**  
O arquivo `src/models/schemas.py` tem imports de `typing` e `pydantic` duplicados nas linhas 13/21 e 19/23.

**Checklist:**
- [ ] Remover linhas duplicadas
- [ ] Remover bloco `try/except` de `Annotated` (desnecessário em Python 3.11+)
- [ ] Rodar `ruff check` e `isort` para validar

---

## Issue #5 — ♻️ Remover routers duplicados

**Título:** `refactor: remover routers duplicados não utilizados`  
**Label:** `task`  
**Branch:** `bugfix/remover-routers-duplicados`  
**Commit:** `refactor: remove routers duplicados (logs_file, logs_text, logs_list)`

**Descrição:**  
Os arquivos `logs_file.py`, `logs_text.py` e `logs_list.py` duplicam endpoints que já existem em `logs.py`. Apenas `logs.py` é importado pelo router.

**Checklist:**
- [ ] Remover `src/api/v1/logs_file.py`
- [ ] Remover `src/api/v1/logs_text.py`
- [ ] Remover `src/api/v1/logs_list.py`
- [ ] Verificar que nenhum import referencia esses arquivos

---

## Issue #6 — ♻️ Corrigir import circular no core/__init__.py

**Título:** `refactor: simplificar core/__init__.py`  
**Label:** `task`  
**Branch:** `bugfix/core-init-circular`  
**Commit:** `refactor: remove import de dependencies do core/__init__.py`

**Descrição:**  
O `src/core/__init__.py` importa `dependencies.py` que puxa `src.ai`, `src.parsers`, `src.repository`. Isso cria dependência circular e faz qualquer import de `src.core.logging` carregar toda a aplicação.

**Checklist:**
- [ ] Remover imports de `dependencies` do `__init__.py`
- [ ] Manter apenas exports de `config`, `logging` e `retry`
- [ ] Verificar que imports diretos (`from src.core.logging import get_logger`) funcionam

---

## Issue #7 — ✨ Implementar camada de controller (MVC)

**Título:** `refactor: separar controller dos endpoints da API`  
**Label:** `enhancement`  
**Branch:** `feature/controller-layer`  
**Commit:** `refactor: separa lógica de controller dos endpoints da API`

**Descrição:**  
Os endpoints em `src/api/v1/logs.py` misturam definição de rotas com lógica de orquestração. Criar camada de controller para separar responsabilidades.

**Checklist:**
- [ ] Criar `src/api/v1/controllers/logs_controller.py`
- [ ] Mover lógica de orquestração (parse → analyze → diagnose → persist) para controller
- [ ] Endpoints ficam apenas com: receber request → chamar controller → retornar response
- [ ] Testes existentes continuam passando

---

## Issue #8 — 📝 Criar User Stories com BDD

**Título:** `docs: adicionar user stories com cenários BDD`  
**Label:** `task`  
**Branch:** `feature/user-stories-bdd`  
**Commit:** `docs: adiciona user stories com cenários BDD`

**Descrição:**  
Documentar as user stories do produto com cenários Gherkin (Given/When/Then) para cada endpoint.

**Checklist:**
- [ ] US-01: Upload de arquivo
- [ ] US-02: Envio via texto
- [ ] US-03: Listagem paginada
- [ ] US-04: Consulta por ID
- [ ] US-05: Remoção
- [ ] US-06: Health check
- [ ] US-07: Qualidade do diagnóstico

---

## Issue #9 — 📝 Criar templates de GitHub Issues

**Título:** `docs: adicionar templates de issues`  
**Label:** `task`  
**Branch:** `feature/github-issues-templates`  
**Commit:** `docs: adiciona templates de issues (bug, feature, task)`

**Descrição:**  
Criar templates padronizados em `.github/ISSUE_TEMPLATE/` para bug reports, feature requests e tasks.

**Checklist:**
- [ ] Template de Bug Report
- [ ] Template de Feature Request
- [ ] Template de Task

---

## Issue #10 — 📝 Criar PRD.md e CONTRIBUTING.md

**Título:** `docs: adicionar PRD.md e CONTRIBUTING.md`  
**Label:** `task`  
**Branch:** `feature/docs-prd-contributing`  
**Commit:** `docs: adiciona PRD.md e CONTRIBUTING.md`

**Descrição:**  
Criar documentação de produto (PRD) e guia de contribuição com instruções de setup, padrões de código e fluxo de trabalho.

**Checklist:**
- [ ] `docs/PRD.md` com visão, endpoints, stack e roadmap
- [ ] `CONTRIBUTING.md` com setup, padrões de branch/commit e qualidade

---

## Issue #11 — 🐛 Corrigir .env.example

**Título:** `fix: corrigir variáveis de ambiente no .env.example`  
**Label:** `bug`  
**Branch:** `bugfix/env-example-prefixo`  
**Commit:** `fix: corrige nomes de variáveis no .env.example`

**Descrição:**  
O `Settings` em `core/config.py` espera variáveis com prefixo `LOGPULSE_` (ex: `LOGPULSE_OLLAMA_BASE_URL`), mas o `.env.example` documenta nomes sem prefixo (ex: `OLLAMA_URL`).

**Checklist:**
- [ ] Renomear variáveis para usar prefixo `LOGPULSE_`
- [ ] Alinhar nomes com os campos do `Settings`
- [ ] Documentar cada variável com comentário
