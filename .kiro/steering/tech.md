---
inclusion: always
---

# Tecnologia — LogPulse IA

## Stack Tecnológica

### Linguagem e Runtime

- **Python 3.11+**: Escolhido pelo ecossistema maduro de IA/ML, bibliotecas de parsing de texto e ferramentas de observabilidade. Requer `tomllib` (stdlib) para configuração.

### Gerenciamento de Dependências

- **pyproject.toml** (PEP 621): Arquivo único para metadados, dependências e configuração de ferramentas
- **pip**: Instalador de pacotes padrão
- **Versionamento de dependências**:
  - Dependências diretas: usar `~=` (compatible release) para permitir patches (ex: `typer~=0.9.0`)
  - Dependências de desenvolvimento: versões exatas com `==` para reprodutibilidade
  - Dependências de IA: versões mínimas com `>=` devido à rápida evolução (ex: `langchain>=0.1.0`)

### Interface de Linha de Comando

- **typer**: Framework moderno para CLIs com validação automática de tipos, documentação integrada e suporte a subcomandos. Preferido sobre `click` pela integração nativa com type hints.

### Parsing de Logs

- **re** (stdlib): Expressões regulares para parsing de formato livre e detecção de padrões
- **pyparsing**: Parser combinator para formatos complexos (Apache/Nginx, Syslog RFC 3164/5424)
- **orjson**: Deserialização JSON de alta performance (até 3x mais rápido que `json` stdlib)

### Integração com IA/LLM

- **langchain**: Framework para orquestração de LLMs, gerenciamento de prompts e chains
- **openai**: Cliente oficial da API OpenAI (GPT-4, GPT-3.5)
- **Ollama** (via HTTP): Suporte a LLMs locais sem dependências adicionais (requests via `httpx`)

### Monitoramento de Arquivos

- **watchdog**: Observação de mudanças em arquivos para modo `--follow` (equivalente a `tail -f`)

### Testes

- **pytest**: Framework de testes com fixtures, parametrização e plugins
- **hypothesis**: Property-based testing para validação de invariantes (ex: round-trip de parsers)
- **pytest-cov**: Cobertura de código integrada ao pytest

### Configuração

- **tomllib** (stdlib Python 3.11+): Parser TOML nativo para leitura de `logpulse.toml`
- **tomli-w**: Serialização TOML para geração de configurações (não disponível na stdlib)

### Qualidade de Código

- **mypy** (strict mode): Verificação de tipos estática
- **black**: Formatação automática de código (line length: 100)
- **isort**: Ordenação de imports (profile: black)
- **ruff**: Linter moderno e rápido (substitui flake8, pylint, pyupgrade)

---

## Arquitetura Técnica

### Padrão Arquitetural

O sistema segue **arquitetura em camadas** com **inversão de dependências** (Dependency Inversion Principle):

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│                   (src/cli/commands.py)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Application Layer                        │
│              (src/analyzer/, src/ai/)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Domain Layer                            │
│         (src/models.py: LogEntry, AnalysisResult)           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Infrastructure Layer                       │
│            (src/sources/, src/parsers/)                     │
└─────────────────────────────────────────────────────────────┘
```

**Fluxo de dados:**
```
LogSource → Parser → LogEntry → Analyzer → AnalysisResult → AIEngine → Diagnóstico
```

### Organização de `src/`

```
src/
├── __init__.py                 # Exporta API pública da biblioteca
├── models.py                   # Modelo de dados central (LogEntry, AnalysisResult, etc.)
├── exceptions.py               # Hierarquia de exceções customizadas
├── config.py                   # Carregamento e validação de logpulse.toml
├── sources/                    # Adaptadores de leitura (Infrastructure)
│   ├── __init__.py
│   ├── base.py                 # Protocol LogSource
│   ├── file.py                 # FileSource, GzipSource
│   └── stdin.py                # StdinSource
├── parsers/                    # Transformação texto → LogEntry (Infrastructure)
│   ├── __init__.py
│   ├── base.py                 # Protocol BaseParser
│   ├── json_parser.py          # JsonParser
│   ├── plaintext.py            # PlaintextParser
│   ├── syslog.py               # SyslogParser
│   ├── apache_nginx.py         # ApacheNginxParser
│   └── auto.py                 # AutoParser (detecção automática)
├── analyzer/                   # Detecção de anomalias (Application)
│   ├── __init__.py
│   ├── detector.py             # Analyzer principal
│   ├── clustering.py           # Agrupamento de mensagens similares
│   └── patterns.py             # Detecção de padrões conhecidos (stack traces)
├── ai/                         # Integração com LLMs (Application)
│   ├── __init__.py
│   ├── base.py                 # Protocol AIEngine
│   ├── openai_engine.py        # OpenAIEngine
│   └── ollama_engine.py        # OllamaEngine
└── cli/                        # Interface de linha de comando (CLI)
    ├── __init__.py
    ├── app.py                  # Typer app principal
    └── commands.py             # Comando `analyze`
```

### Princípios de Design

1. **Dependency Inversion**: Camadas superiores dependem de abstrações (Protocols), não de implementações concretas
2. **Single Responsibility**: Cada módulo tem uma responsabilidade clara e única
3. **Open/Closed**: Novos parsers e sources podem ser adicionados sem modificar código existente
4. **Interface Segregation**: Protocols pequenos e focados (`LogSource`, `BaseParser`, `AIEngine`)

---

## Modelo de Dados Central

### LogEntry

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    """Níveis de severidade normalizados."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Unidade atômica de log normalizada."""
    timestamp: datetime           # sempre com timezone (UTC se não especificado)
    level: SeverityLevel          # nível normalizado
    message: str                  # não vazia (validado no __post_init__)
    source: str                   # identificador da LogSource (ex: "file:app.log")
    raw: str | None = None        # linha original (para entradas não parseadas)
    timestamp_inferred: bool = False  # True se timestamp foi inferido
    level_inferred: bool = False      # True se level foi inferido
    extra: dict = field(default_factory=dict)  # campos adicionais (JSON, syslog)
    
    def __post_init__(self):
        """Valida invariantes do LogEntry."""
        if not self.message:
            raise ValueError("LogEntry.message não pode ser vazio")
        if self.timestamp.tzinfo is None:
            # Força timezone UTC se não especificado
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
```

### AnalysisResult

```python
@dataclass
class Anomaly:
    """Anomalia detectada no log stream."""
    type: str                     # "spike", "pattern", "sequence"
    severity: SeverityLevel
    description: str
    entries: list[LogEntry]       # entradas relacionadas
    timestamp_range: tuple[datetime, datetime]

@dataclass
class AnalysisResult:
    """Resultado da análise de um log stream."""
    anomalies: list[Anomaly]
    patterns: dict[str, int]      # padrão → contagem
    distribution: dict[SeverityLevel, int]  # distribuição por nível
    summary: str                  # resumo textual
    total_entries: int
    time_range: tuple[datetime, datetime] | None
```

---

## Convenções de Código

### Tipagem Estática

- **mypy strict mode obrigatório**: `mypy --strict src/`
- **Sem `Any` sem justificativa**: Documentar no comentário quando inevitável
- **Protocols sobre ABCs**: Preferir `typing.Protocol` para duck typing
- **Type hints em todas as assinaturas**: Funções, métodos, lambdas
- **Generics explícitos**: `list[str]`, `dict[str, int]`, nunca `list`, `dict`

```python
# ✅ Correto
def parse_line(line: str, source: str) -> LogEntry | None:
    ...

# ❌ Incorreto
def parse_line(line, source):  # sem type hints
    ...
```

### Tratamento de Erros

#### Hierarquia de Exceções

```python
# src/exceptions.py
class LogPulseError(Exception):
    """Exceção base do LogPulse IA."""
    pass

class ConfigError(LogPulseError):
    """Erro de configuração (logpulse.toml inválido)."""
    pass

class SourceError(LogPulseError):
    """Erro ao ler fonte de log (arquivo não encontrado, permissão negada)."""
    pass

class ParserError(LogPulseError):
    """Erro ao parsear linha de log."""
    pass

class AIEngineError(LogPulseError):
    """Erro ao comunicar com LLM (API key inválida, timeout)."""
    pass
```

#### Regras de Tratamento

1. **Fail fast em configuração**: Erros de config/setup devem abortar imediatamente
2. **Resiliente em parsing**: Parsers devem registrar erros mas continuar processamento
3. **Graceful degradation em IA**: Se AI falhar, retornar análise sem diagnóstico IA
4. **Mensagens descritivas**: Incluir contexto (arquivo, linha, valor inválido)

```python
# ✅ Correto: erro descritivo
if not path.exists():
    raise SourceError(f"Arquivo não encontrado: {path}")

# ❌ Incorreto: erro genérico
if not path.exists():
    raise FileNotFoundError()
```

### Formatação e Estilo

- **black** com `line-length = 100` (configurado em `pyproject.toml`)
- **isort** com `profile = "black"`
- **ruff** com regras:
  - `E` (pycodestyle errors)
  - `F` (pyflakes)
  - `I` (isort)
  - `N` (pep8-naming)
  - `UP` (pyupgrade)
  - `RUF` (ruff-specific)

### Nomenclatura

- **Variáveis e funções**: `snake_case` em inglês
- **Classes**: `PascalCase` em inglês
- **Constantes**: `UPPER_SNAKE_CASE`
- **Módulos**: `snake_case` (ex: `apache_nginx.py`)
- **Privado**: prefixo `_` (ex: `_internal_helper()`)

### Docstrings

- **Idioma**: Português para funções e classes públicas
- **Formato**: Google Style (suportado por sphinx e mkdocs)
- **Obrigatório para**: Funções públicas, classes, métodos públicos, módulos

```python
def analyze(entries: list[LogEntry], config: AnalyzerConfig) -> AnalysisResult:
    """Analisa um stream de logs e detecta anomalias.
    
    Args:
        entries: Lista de entradas de log normalizadas.
        config: Configuração do analisador (thresholds, janelas de tempo).
    
    Returns:
        Resultado da análise contendo anomalias, padrões e resumo.
    
    Raises:
        ValueError: Se entries estiver vazia.
    
    Example:
        >>> entries = [LogEntry(...), LogEntry(...)]
        >>> result = analyze(entries, AnalyzerConfig())
        >>> print(result.summary)
    """
    ...
```

---

## Padrões de Testes

### Estrutura de Testes

- **Espelhamento**: `tests/` espelha estrutura de `src/`
- **Nomenclatura**: `test_<módulo>.py` para cada `<módulo>.py`
- **Fixtures**: Centralizadas em `tests/conftest.py`

```
tests/
├── conftest.py                 # Fixtures compartilhadas
├── test_models.py
├── test_config.py
├── sources/
│   ├── test_file.py
│   └── test_stdin.py
├── parsers/
│   ├── test_json_parser.py
│   └── test_plaintext.py
├── analyzer/
│   └── test_detector.py
└── cli/
    └── test_commands.py
```

### Tipos de Testes

#### 1. Testes Unitários (pytest)

- **Escopo**: Função/método isolado
- **Mocks**: Usar `unittest.mock` ou `pytest-mock`
- **Cobertura mínima**: 80% de line coverage

```python
def test_parse_json_valid_entry(json_parser):
    """Testa parsing de JSON válido."""
    line = '{"timestamp": "2024-01-01T10:00:00Z", "level": "INFO", "message": "test"}'
    entry = json_parser.parse(line, source="test")
    
    assert entry.level == SeverityLevel.INFO
    assert entry.message == "test"
    assert not entry.timestamp_inferred
```

#### 2. Testes de Integração (pytest)

- **Escopo**: Múltiplos componentes (ex: Source + Parser + Analyzer)
- **Fixtures**: Arquivos `.log` reais em `logs/fixtures/`

```python
def test_analyze_real_log_file(tmp_path):
    """Testa análise end-to-end de arquivo real."""
    log_file = tmp_path / "app.log"
    log_file.write_text(SAMPLE_LOG_CONTENT)
    
    source = FileSource(log_file)
    parser = AutoParser()
    entries = [parser.parse(line, str(log_file)) for line in source]
    result = analyze(entries)
    
    assert result.total_entries > 0
    assert len(result.anomalies) >= 0
```

#### 3. Property-Based Testing (hypothesis)

- **Escopo**: Invariantes e propriedades (ex: round-trip de parsers)
- **Uso**: Validação de parsers, serializers, normalização

```python
from hypothesis import given, strategies as st

@given(st.datetimes(timezones=st.just(timezone.utc)))
def test_log_entry_timestamp_always_has_timezone(dt):
    """Propriedade: LogEntry sempre tem timezone no timestamp."""
    entry = LogEntry(
        timestamp=dt,
        level=SeverityLevel.INFO,
        message="test",
        source="test"
    )
    assert entry.timestamp.tzinfo is not None

@given(st.text(min_size=1))
def test_json_parser_roundtrip(message):
    """Propriedade: JSON parser + pretty printer = identidade."""
    entry = LogEntry(
        timestamp=datetime.now(timezone.utc),
        level=SeverityLevel.INFO,
        message=message,
        source="test"
    )
    json_line = pretty_print_json(entry)
    parsed = json_parser.parse(json_line, "test")
    
    assert parsed.message == entry.message
    assert parsed.level == entry.level
```

### Cobertura de Código

- **Meta**: 80% de line coverage mínimo
- **Comando**: `pytest --cov=src --cov-report=html --cov-report=term`
- **CI**: Bloquear merge se cobertura cair abaixo de 80%

### Fixtures Compartilhadas

```python
# tests/conftest.py
import pytest
from src.models import LogEntry, SeverityLevel
from datetime import datetime, timezone

@pytest.fixture
def sample_log_entry():
    """LogEntry de exemplo para testes."""
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        level=SeverityLevel.INFO,
        message="Sample log message",
        source="test"
    )

@pytest.fixture
def json_parser():
    """Parser JSON configurado."""
    from src.parsers.json_parser import JsonParser
    return JsonParser()
```

---

## Padrão de Logs Internos

O LogPulse IA gera logs internos para debugging e auditoria usando **structlog**.

### Configuração

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
```

### Níveis de Log

| Nível    | Quando usar                                      |
|----------|--------------------------------------------------|
| DEBUG    | Detalhes de parsing, decisões internas           |
| INFO     | Início/fim de análise, arquivos processados      |
| WARNING  | Linhas não parseadas, configuração faltando      |
| ERROR    | Falha ao ler arquivo, erro de API               |
| CRITICAL | Erro irrecuperável (corrupção de dados, OOM)    |

### Exemplo

```python
logger.info("analysis_started", source=source_path, entries_count=len(entries))
logger.warning("line_parse_failed", line_number=42, raw_line=line)
logger.error("ai_engine_failed", error=str(e), model=config.ai.model)
```

---

## Padrão de Configuração

### Estrutura de `logpulse.toml`

```toml
[ai]
model = "gpt-4o"                # ou "gpt-3.5-turbo"
# endpoint = "http://localhost:11434"  # para Ollama local
temperature = 0.7
max_tokens = 1000

[parser]
format = "auto"                 # auto | json | plaintext | syslog | apache
# custom_regex = "(?P<timestamp>\\S+) (?P<level>\\w+) (?P<message>.*)"

[analyzer]
spike_threshold = 10            # erros/minuto para detectar spike
window_seconds = 60             # janela de tempo para spikes
min_cluster_size = 3            # mínimo de mensagens para formar cluster

[output]
format = "text"                 # text | json
color = true                    # colorir output no terminal
```

### Precedência de Configuração

1. **Flags CLI** (maior precedência)
2. **Variáveis de ambiente** (`LOGPULSE_API_KEY`, `LOGPULSE_MODEL`)
3. **`./logpulse.toml`** (diretório de trabalho)
4. **`~/.config/logpulse/logpulse.toml`** (global do usuário)
5. **Defaults hardcoded** (menor precedência)

---

## Automações e CI

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: black --check src/ tests/
      - run: isort --check src/ tests/
      - run: mypy --strict src/
      - run: pytest --cov=src --cov-report=xml --cov-fail-under=80
      - uses: codecov/codecov-action@v3  # upload cobertura
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Bloqueio de Merge

- **Requer**: Todos os checks do CI passando (lint, types, tests, coverage ≥80%)
- **Requer**: 1 aprovação de code review
- **Requer**: Branch atualizada com `develop` (Git Flow)

---

## Documentação Técnica

### Quando Documentar

- **Sempre**: Funções públicas, classes, módulos
- **Quando necessário**: Algoritmos complexos, decisões não óbvias, workarounds
- **Nunca**: Código auto-explicativo, getters/setters triviais

### Formato de Docstrings

```python
def complex_algorithm(data: list[int], threshold: float) -> dict[str, Any]:
    """Descrição curta em uma linha.
    
    Descrição detalhada opcional explicando o algoritmo, complexidade,
    casos especiais, etc.
    
    Args:
        data: Lista de valores inteiros a processar.
        threshold: Limiar para filtragem (0.0 a 1.0).
    
    Returns:
        Dicionário com chaves 'result', 'filtered_count', 'stats'.
    
    Raises:
        ValueError: Se threshold estiver fora do intervalo [0, 1].
    
    Note:
        Complexidade: O(n log n) devido à ordenação interna.
    
    Example:
        >>> complex_algorithm([1, 2, 3], 0.5)
        {'result': [...], 'filtered_count': 2, 'stats': {...}}
    """
    ...
```

### Comentários Inline

```python
# ✅ Correto: explica decisão não óbvia
# Usamos orjson em vez de json stdlib para performance em logs grandes (>1GB)
data = orjson.loads(line)

# ❌ Incorreto: redundante com o código
# Incrementa contador
counter += 1
```
