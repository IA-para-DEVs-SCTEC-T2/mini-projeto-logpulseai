# Guia de Contribuição — LogPulse IA

## Pré-requisitos

- Python 3.11+
- pip
- Ollama instalado e rodando (`ollama serve`)
- Modelo LLaMA 3 baixado (`ollama pull llama3`)

## Setup do Ambiente

```bash
# Clone o repositório
git clone <url-do-repo>
cd mini-projeto-logpulseai

# Instale em modo desenvolvimento
pip install -e ".[dev]"

# Copie o arquivo de ambiente
cp .env.example .env

# Inicie o Ollama
ollama serve
```

## Rodando a API

```bash
uvicorn src.api.app:app --reload --port 8000
```

Acesse a documentação em: http://localhost:8000/docs

## Rodando os Testes

```bash
# Todos os testes com cobertura
pytest

# Apenas um módulo
pytest tests/parsers/

# Com output verbose
pytest -v
```

## Padrão de Branches

Apenas dois prefixos são aceitos:

| Padrão | Quando usar |
|--------|-------------|
| `feature/<nome>` | Nova funcionalidade |
| `bugfix/<nome>` | Correção de bug |

Regras do `<nome>`:
- Apenas letras minúsculas, números e hífens
- Mínimo 3 caracteres
- Sem espaços, underscores ou maiúsculas

```bash
# Exemplos válidos
git checkout -b feature/endpoint-logs-file
git checkout -b bugfix/correcao-timeout

# Exemplos inválidos
git checkout -b hotfix/bug       # prefixo não permitido
git checkout -b feature/AB       # maiúsculas
git checkout -b feature/ab       # menos de 3 caracteres
```

## Padrão de Commits

Formato: `<tipo>: <descrição>` ou `<tipo>(escopo): <descrição>`

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `refactor` | Melhoria sem mudar função |

```bash
# Exemplos válidos
git commit -m "feat: adiciona endpoint POST api/v1/logs/file"
git commit -m "fix: corrige parsing de stacktrace Java"
git commit -m "docs: atualiza README com instruções"
git commit -m "refactor: simplifica lógica do analyzer"
```

> ⚠️ Apenas estes 4 tipos são aceitos pelo CI.

## Pull Requests

1. Crie branch a partir de `main`
2. Faça commits seguindo o padrão acima
3. Abra PR com título claro
4. Aguarde **1 aprovação** de outro colaborador
5. **Nunca aprove seu próprio PR**

```bash
gh pr create \
  --title "feat: adiciona endpoint de upload de arquivo" \
  --body "Implementa POST api/v1/logs/file com validação Pydantic." \
  --base main
```

## Estrutura do Código

```
src/
├── api/           # Rotas e controllers FastAPI
│   └── v1/       # Endpoints versionados
├── services/      # Lógica de negócio
├── parsers/       # Parsing de logs (Drain3)
├── ai/            # Integração com Ollama/LLaMA 3
├── analyzer/      # Detecção de anomalias
├── repository/    # Persistência (SQLite)
├── models/        # Schemas Pydantic
├── core/          # Config, logging, retry
└── exceptions.py  # Hierarquia de exceções
```

## Qualidade de Código

```bash
# Lint
ruff check src/ tests/

# Formatação
black src/ tests/
isort src/ tests/

# Type checking
mypy --strict src/

# Testes com cobertura (mínimo 30%)
pytest --cov=src --cov-fail-under=30
```

## Regras Importantes

- Cobertura mínima de testes: **30%**
- Docstrings em português (Google Style)
- Type hints em todas as assinaturas
- Nunca commitar diretamente na `main`
