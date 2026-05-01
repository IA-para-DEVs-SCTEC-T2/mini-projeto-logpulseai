# LogPulse IA

> Investigue problemas rapidamente através dos seus logs.

## Objetivo

O **LogPulse IA** é uma ferramenta de linha de comando e biblioteca Python para ingestão, análise e investigação inteligente de logs. Com suporte a IA, permite identificar a causa raiz de incidentes de forma rápida, reduzindo o MTTR (Mean Time To Resolution) em ambientes de produção.

## Funcionalidades

- Leitura de logs de arquivos locais (`.log`, `.txt`, `.gz`) e via stdin/pipe
- Parsing automático de JSON estruturado, Apache/Nginx, Syslog e formato livre
- Detecção automática de anomalias e spikes de erros
- Investigação com IA: hipóteses de causa raiz e sugestões de ação
- Suporte a LLMs locais via Ollama e APIs externas (OpenAI)
- CLI intuitiva: `logpulse analyze <fonte>`

## Estrutura do Projeto

```
logpulse-ia/
├── src/                  # Código-fonte principal
│   ├── sources/          # Adaptadores de fonte de log (LogSource)
│   ├── parsers/          # Parsers por formato (JSON, plaintext, syslog)
│   ├── analyzer/         # Motor de detecção de anomalias
│   ├── ai/               # AI Engine (integração com LLMs)
│   └── cli/              # Interface de linha de comando
├── tests/                # Testes automatizados
├── logs/                 # Arquivos de log para testes e exemplos
├── docs/                 # Documentação adicional
├── logpulse.toml         # Configuração do projeto (exemplo)
└── README.md
```

## Instalação

> 🚧 Em desenvolvimento — instruções de instalação serão adicionadas em breve.

```bash
# Pré-requisitos: Python 3.11+
pip install logpulse-ia
```

## Uso Rápido

```bash
# Analisar um arquivo de log
logpulse analyze app.log

# Analisar via pipe
cat app.log | logpulse analyze -

# Analisar com suporte de IA
logpulse analyze app.log --ai

# Saída em JSON
logpulse analyze app.log --output json
```

## Configuração

Crie um arquivo `logpulse.toml` no diretório do projeto ou em `~/.config/logpulse/logpulse.toml`:

```toml
[ai]
model = "gpt-4o"
# ou para LLM local:
# endpoint = "http://localhost:11434"

[parser]
format = "json"  # json | plaintext | syslog | auto
```

A variável de ambiente `LOGPULSE_API_KEY` tem precedência sobre o arquivo de configuração.


## GitHub Flow

**Branches:**
- `main` → protegida, sempre estável
- `feature/*` → novas funcionalidades
- `bugfix/*` → correções de bugs

**Fluxo:**
```
main → feature/nome → PR (1 aprovação) → merge → main
main → bugfix/nome → PR (1 aprovação) → merge → main
```

**Regras:**
- ❌ Nunca commite diretamente em `main`
- ✅ Commits semânticos: `feat:`, `fix:`, `docs:`, `refactor:`
- ✅ Todo merge via Pull Request com 1 aprovação mínima

## Status

🚧 Em desenvolvimento ativo

