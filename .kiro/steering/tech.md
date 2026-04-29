---
inclusion: always
---

# Tecnologia — LogPulse IA

## Stack

- **Linguagem:** Python 3.11+
- **Gerenciador de pacotes:** `pip` com `pyproject.toml`
- **CLI:** `typer` ou `click`
- **Parsing de logs:** `re`, `pyparsing`, `orjson`
- **IA/LLM:** `langchain`, `openai`, suporte a Ollama (LLM local)
- **Monitoramento de arquivos:** `watchdog`
- **Testes:** `pytest` com property-based testing via `hypothesis`
- **Configuração:** `tomllib` (stdlib Python 3.11+)
- **Qualidade de código:** `mypy` (strict), `black`, `isort`, `ruff`

## Arquitetura

O sistema é organizado em camadas com responsabilidades bem definidas:

```
LogSource → Parser → Log_Entry → Analyzer → Analysis_Result → AI_Engine → Diagnóstico
```

### Módulos em `src/`

| Módulo      | Responsabilidade                                           |
|-------------|------------------------------------------------------------|
| `sources/`  | Adaptadores de leitura (arquivo, stdin, .gz)               |
| `parsers/`  | Transformação de texto bruto em `Log_Entry` estruturado    |
| `analyzer/` | Detecção de anomalias, spikes, agrupamento de padrões      |
| `ai/`       | Integração com LLMs para diagnóstico e hipóteses           |
| `cli/`      | Interface de linha de comando (`logpulse analyze <fonte>`) |

## Modelo de Dados Central

```python
@dataclass
class LogEntry:
    timestamp: datetime           # sempre com timezone
    level: SeverityLevel          # DEBUG | INFO | WARNING | ERROR | CRITICAL
    message: str                  # não vazia
    source: str                   # identificador da LogSource
    raw: str | None = None        # linha original (para entradas não parseadas)
    timestamp_inferred: bool = False
    level_inferred: bool = False
    extra: dict = field(default_factory=dict)  # campos adicionais do JSON/syslog
```

## Convenções de Código

- Tipagem estática com `mypy` (strict mode) — sem `Any` sem justificativa
- Formatação com `black` e `isort`
- Linting com `ruff`
- Docstrings em português para funções e classes públicas
- Nomes de variáveis e funções em inglês (`snake_case`)
- Classes em `PascalCase`
- Testes espelham a estrutura de `src/` dentro de `tests/`
