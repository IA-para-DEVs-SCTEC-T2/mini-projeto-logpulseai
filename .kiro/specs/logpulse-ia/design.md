# Design Técnico — LogPulse IA

## Visão Geral

Este documento descreve as decisões de arquitetura, interfaces entre módulos e contratos de dados do LogPulse IA. O objetivo é guiar a implementação de forma consistente com os requisitos definidos em `requirements.md`.

---

## Arquitetura em Camadas

O sistema segue um pipeline linear de transformação de dados:

```
LogSource → Parser → LogEntry → Analyzer → AnalysisResult → AIEngine → Diagnóstico
                                                    ↑
                                               CLI / Config
```

Cada camada tem uma única responsabilidade e se comunica com a próxima via tipos bem definidos. Nenhuma camada conhece os detalhes internos da anterior.

---

## Estrutura de Módulos

```
src/
├── sources/
│   ├── __init__.py
│   ├── base.py          # Protocolo LogSource
│   ├── file_source.py   # Leitura de arquivo local e .gz
│   └── stdin_source.py  # Leitura via stdin/pipe
├── parsers/
│   ├── __init__.py
│   ├── base.py          # Protocolo Parser e PrettyPrinter
│   ├── json_parser.py   # Parsing de JSON estruturado
│   ├── plaintext_parser.py  # Formato livre com regex
│   ├── syslog_parser.py     # RFC 3164/5424
│   ├── apache_parser.py     # Apache/Nginx Combined Log Format
│   └── auto_parser.py       # Detecção automática de formato
├── analyzer/
│   ├── __init__.py
│   ├── analyzer.py      # Orquestrador principal
│   ├── spike_detector.py    # Detecção de spikes de erro
│   ├── pattern_grouper.py   # Agrupamento de mensagens similares
│   └── models.py        # AnalysisResult, AnomalyEvent, ErrorCluster
├── ai/
│   ├── __init__.py
│   ├── engine.py        # AIEngine — orquestrador
│   ├── openai_client.py # Integração com OpenAI API
│   ├── ollama_client.py # Integração com Ollama (LLM local)
│   └── prompts.py       # Templates de prompt
├── cli/
│   ├── __init__.py
│   └── main.py          # Entrypoint Typer
├── config.py            # Carregamento de logpulse.toml
└── models.py            # LogEntry, SeverityLevel (tipos centrais)
```

---

## Modelos de Dados

### `SeverityLevel`

```python
from enum import Enum

class SeverityLevel(str, Enum):
    DEBUG    = "DEBUG"
    INFO     = "INFO"
    WARNING  = "WARNING"
    ERROR    = "ERROR"
    CRITICAL = "CRITICAL"
```

Mapeamento de aliases para normalização:

| Alias recebido | Valor canônico |
|----------------|----------------|
| `WARN`         | `WARNING`      |
| `ERR`          | `ERROR`        |
| `FATAL`        | `CRITICAL`     |
| `TRACE`        | `DEBUG`        |

### `LogEntry`

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class LogEntry:
    timestamp: datetime           # sempre com timezone (UTC se não especificado)
    level: SeverityLevel
    message: str                  # não vazia
    source: str                   # identificador da LogSource
    raw: str | None = None        # linha original
    timestamp_inferred: bool = False
    level_inferred: bool = False
    extra: dict = field(default_factory=dict)
```

### `AnalysisResult`

```python
@dataclass
class AnalysisResult:
    source: str
    total_entries: int
    level_distribution: dict[SeverityLevel, int]
    time_distribution: dict[datetime, int]   # janelas de 1 minuto
    spikes: list[SpikeEvent]
    error_clusters: list[ErrorCluster]
    patterns: list[PatternGroup]
    insufficient_data: bool = False
```

### `SpikeEvent`

```python
@dataclass
class SpikeEvent:
    window_start: datetime
    window_end: datetime
    count: int
    level: SeverityLevel
```

### `ErrorCluster`

```python
@dataclass
class ErrorCluster:
    entries: list[LogEntry]
    cluster_type: str   # "python_traceback" | "java_stacktrace" | "go_panic" | "generic"
    first_seen: datetime
    last_seen: datetime
```

### `PatternGroup`

```python
@dataclass
class PatternGroup:
    template: str        # mensagem com partes variáveis substituídas por <*>
    count: int
    sample: LogEntry
    level: SeverityLevel
```

### `Diagnosis`

```python
@dataclass
class Hypothesis:
    description: str
    probability: str     # "alta" | "média" | "baixa"
    investigation_steps: list[str]

@dataclass
class Diagnosis:
    summary: str
    hypotheses: list[Hypothesis]   # mínimo 3 quando há spike/cluster
    raw_prompt: str | None = None  # para debug
```

---

## Interfaces (Protocolos)

### `LogSource`

```python
from typing import Protocol, Iterator

class LogSource(Protocol):
    @property
    def source_id(self) -> str: ...

    def read(self) -> Iterator[str]:
        """Produz linhas brutas do log, uma por vez."""
        ...

    def follow(self) -> Iterator[str]:
        """Modo tail -f: produz linhas continuamente até interrupção."""
        ...
```

### `Parser`

```python
class Parser(Protocol):
    def parse(self, line: str, source: str) -> LogEntry:
        """Transforma uma linha bruta em LogEntry."""
        ...

    def detect(self, line: str) -> bool:
        """Retorna True se este parser reconhece o formato da linha."""
        ...
```

### `PrettyPrinter`

```python
class PrettyPrinter(Protocol):
    def format(self, entry: LogEntry) -> str:
        """Serializa um LogEntry para exibição ou saída."""
        ...
```

### `LLMClient`

```python
class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Envia prompt e retorna resposta do LLM."""
        ...
```

---

## Fluxo de Execução — `logpulse analyze <fonte>`

```
1. CLI recebe argumentos e carrega Config
2. Config resolve: logpulse.toml local → ~/.config/logpulse/logpulse.toml → env vars
3. CLI instancia o LogSource adequado (FileSource ou StdinSource)
4. CLI instancia o Parser adequado (ou AutoParser se format=auto)
5. LogSource.read() → Iterator[str] de linhas brutas
6. Para cada linha: Parser.parse(line) → LogEntry
7. Analyzer.analyze(entries) → AnalysisResult
8. Se --ai: AIEngine.diagnose(result) → Diagnosis
9. PrettyPrinter.format() → stdout
10. CLI retorna exit code (0, 1 ou 2)
```

---

## Detecção Automática de Formato (`AutoParser`)

O `AutoParser` inspeciona as primeiras linhas do stream (até 10) para decidir qual parser usar:

1. Tenta `json.loads()` — se válido, usa `JsonParser`
2. Tenta regex do Syslog RFC 3164 — se match, usa `SyslogParser`
3. Tenta regex do Apache Combined Log Format — se match, usa `ApacheParser`
4. Fallback: `PlaintextParser`

Uma vez decidido o formato, o mesmo parser é usado para todo o stream.

---

## Detecção de Anomalias

### Spike Detector

- Janela deslizante de 60 segundos
- Threshold: 10 entradas ERROR ou CRITICAL na janela
- Implementação: bucket por minuto, varredura O(n)

### Pattern Grouper

- Algoritmo: drain3 ou implementação própria baseada em tokenização
- Tokens numéricos, IPs, UUIDs e hashes são substituídos por `<*>` para formar o template
- Entradas com template idêntico são agrupadas no mesmo `PatternGroup`

### Stack Trace / Traceback Detector

Detecta início de stack trace por padrões:
- Python: linha começa com `Traceback (most recent call last):`
- Java: linha contém `Exception in thread` ou `at com.` / `at java.`
- Go: linha contém `goroutine` seguida de `[running]`

Linhas subsequentes são acumuladas no mesmo `ErrorCluster` até encontrar uma linha que não corresponda ao padrão de continuação.

---

## Integração com LLMs

### Seleção de cliente

```
Config.ai.endpoint definido → OllamaClient
Config.ai.model definido (sem endpoint) → OpenAIClient
Nenhum → erro descritivo com instrução de configuração
```

### Estrutura do prompt

O prompt enviado ao LLM é montado em `prompts.py` com:
1. Contexto do sistema (papel do assistente)
2. Resumo do `AnalysisResult` (distribuição, spikes, clusters)
3. Amostras representativas de `LogEntry` (máximo 20 entradas)
4. Instrução de saída estruturada (JSON com `summary` e `hypotheses`)

O LLM nunca recebe o log completo — apenas o `AnalysisResult` e amostras, para evitar vazamento de dados sensíveis e reduzir tokens.

### Timeout e resiliência

- Timeout padrão: 30 segundos por chamada
- Sem retry automático (falha rápida com mensagem descritiva)
- Erros de rede ou API retornam erro com código de saída `1`

---

## Configuração (`config.py`)

### Precedência (maior para menor)

```
Variável de ambiente (LOGPULSE_API_KEY)
  → logpulse.toml no diretório atual
    → ~/.config/logpulse/logpulse.toml
```

### Schema do `logpulse.toml`

```toml
[ai]
model    = "gpt-4o"          # modelo OpenAI
endpoint = ""                # endpoint Ollama (ex: http://localhost:11434)
timeout  = 30                # segundos

[parser]
format  = "auto"             # auto | json | plaintext | syslog | apache
encoding = "utf-8"           # encoding padrão dos arquivos

[analyzer]
spike_threshold = 10         # erros por janela para disparar spike
spike_window_seconds = 60    # tamanho da janela em segundos
```

### Modelo Python

```python
@dataclass
class AIConfig:
    model: str = "gpt-4o"
    endpoint: str = ""
    timeout: int = 30
    api_key: str = ""        # preenchido via env var

@dataclass
class ParserConfig:
    format: str = "auto"
    encoding: str = "utf-8"

@dataclass
class AnalyzerConfig:
    spike_threshold: int = 10
    spike_window_seconds: int = 60

@dataclass
class Config:
    ai: AIConfig = field(default_factory=AIConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    analyzer: AnalyzerConfig = field(default_factory=AnalyzerConfig)
```

---

## Tratamento de Encoding

- Encoding padrão: `utf-8`
- Configurável via `parser.encoding` no `logpulse.toml`
- Erros de decodificação: substituição por `\ufffd` (não interrompe o stream)
- Arquivos `.gz`: descomprimidos em memória com `gzip.open()`, mesmo encoding aplicado

---

## CLI — Mapeamento de Argumentos

```
logpulse analyze <fonte> [opções]

Argumentos:
  fonte          Caminho do arquivo, diretório ou "-" para stdin

Opções:
  --ai           Ativa o AIEngine após a análise
  --follow       Modo monitoramento contínuo (tail -f)
  --output       Formato de saída: "text" (padrão) | "json"
  --format       Formato do parser: "auto" | "json" | "plaintext" | "syslog" | "apache"
  --config       Caminho alternativo para logpulse.toml
```

### Códigos de saída

| Código | Condição                                              |
|--------|-------------------------------------------------------|
| `0`    | Análise concluída sem anomalias críticas              |
| `1`    | Erro de entrada, configuração ou falha no LLM         |
| `2`    | Anomalias críticas detectadas (spike ou error cluster)|

---

## Decisões de Design

### Por que `Protocol` em vez de `ABC`?

Protocolos permitem duck typing estrutural — qualquer classe que implemente os métodos corretos satisfaz o contrato, sem herança explícita. Isso facilita testes com mocks simples e evita acoplamento desnecessário.

### Por que `dataclass` em vez de `pydantic`?

`dataclass` é stdlib e suficiente para os modelos internos. `pydantic` seria adicionado apenas se houvesse necessidade de validação de entrada externa (ex: API REST), o que está fora do escopo atual.

### Por que o LLM recebe apenas o `AnalysisResult` e não o log completo?

Dois motivos: (1) logs de produção frequentemente contêm dados sensíveis (tokens, senhas em query strings, PII); (2) reduz drasticamente o consumo de tokens e a latência da chamada.

### Por que `AutoParser` inspeciona apenas as primeiras 10 linhas?

Suficiente para detectar o formato com alta confiança, sem bloquear o início do processamento em arquivos grandes.
