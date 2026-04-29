---
inclusion: always
---

# Contexto do Projeto — LogPulse IA

## Visão Geral

**LogPulse IA** é uma ferramenta CLI e biblioteca Python para ingestão, análise e investigação inteligente de logs. O objetivo é reduzir o MTTR (Mean Time To Resolution) de incidentes em produção com suporte de IA.

## Linguagem e Stack

- **Linguagem:** Python 3.11+
- **Gerenciador de pacotes:** `pip` com `pyproject.toml`
- **CLI:** `typer` ou `click`
- **Parsing de logs:** `re`, `pyparsing`, `orjson`
- **IA/LLM:** `langchain`, `openai`, suporte a Ollama (LLM local)
- **Monitoramento de arquivos:** `watchdog`
- **Testes:** `pytest` com property-based testing via `hypothesis`
- **Configuração:** `tomllib` (stdlib Python 3.11+)

## Arquitetura

O sistema é organizado em camadas com responsabilidades bem definidas:

```
LogSource → Parser → Log_Entry → Analyzer → Analysis_Result → AI_Engine → Diagnóstico
```

### Módulos em `src/`

| Módulo         | Responsabilidade                                              |
|----------------|---------------------------------------------------------------|
| `sources/`     | Adaptadores de leitura (arquivo, stdin, .gz)                  |
| `parsers/`     | Transformação de texto bruto em `Log_Entry` estruturado       |
| `analyzer/`    | Detecção de anomalias, spikes, agrupamento de padrões         |
| `ai/`          | Integração com LLMs para diagnóstico e hipóteses              |
| `cli/`         | Interface de linha de comando (`logpulse analyze <fonte>`)    |

### Modelo de dados central

```python
@dataclass
class LogEntry:
    timestamp: datetime          # sempre com timezone
    level: SeverityLevel         # DEBUG | INFO | WARNING | ERROR | CRITICAL
    message: str                 # não vazia
    source: str                  # identificador da LogSource
    raw: str | None = None       # linha original (para entradas não parseadas)
    timestamp_inferred: bool = False
    level_inferred: bool = False
    extra: dict = field(default_factory=dict)  # campos adicionais do JSON/syslog
```

## Convenções de Código

- Tipagem estática com `mypy` (strict mode)
- Formatação com `black` e `isort`
- Linting com `ruff`
- Docstrings em português para funções públicas
- Nomes de variáveis e funções em inglês (snake_case)
- Classes em PascalCase

## Configuração

O sistema carrega configurações de `logpulse.toml` no diretório atual ou em `~/.config/logpulse/logpulse.toml`. A variável de ambiente `LOGPULSE_API_KEY` tem precedência sobre o arquivo de configuração.

## Comandos Principais

```bash
logpulse analyze <fonte>          # analisa logs de arquivo ou stdin (-)
logpulse analyze <fonte> --ai     # análise com suporte de IA
logpulse analyze <fonte> --follow # monitoramento contínuo (tail -f)
logpulse analyze <fonte> --output json  # saída em JSON
logpulse --help                   # documentação de uso
```

## Códigos de Saída da CLI

| Código | Significado                                      |
|--------|--------------------------------------------------|
| `0`    | Análise concluída sem erros                      |
| `1`    | Erro de entrada ou configuração                  |
| `2`    | Anomalias críticas detectadas no Log_Stream      |
