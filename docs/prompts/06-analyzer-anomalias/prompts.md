# Prompts — Tarefa 5: Implementar Analyzer de Anomalias

## Contexto

Esta documentação registra os prompts e decisões tomadas durante a implementação da Tarefa 5 do LogPulse IA: o módulo de análise de anomalias (`src/analyzer/`).

---

## Prompt 1 — Criar interface abstrata LogAnalyzer

**Prompt:**
> Crie uma interface abstrata `LogAnalyzer` em `src/analyzer/base.py` usando ABC do Python. O método abstrato `analyze` deve receber `entries: list[LogEntry]` e `templates: list[LogTemplate]` e retornar `AnalysisResult`. Use tipagem completa com type hints e docstrings em português no estilo Google.

**Resultado:**
- Criado `src/analyzer/base.py` com classe `LogAnalyzer(ABC)`
- Método abstrato `analyze()` com assinatura completa
- Impossível instanciar diretamente (lança `TypeError`)

---

## Prompt 2 — Implementar AnomalyDetector

**Prompt:**
> Implemente `AnomalyDetector` em `src/analyzer/detector.py` como subclasse concreta de `LogAnalyzer`. O detector deve:
> - Retornar `insufficient_data=True` se houver menos de 2 entradas
> - Calcular distribuição de severidade (contagem por `SeverityLevel`)
> - Calcular `error_count` (ERROR + CRITICAL) e `warning_count`
> - Detectar spikes de erro usando janela deslizante de 60s com threshold ≥10
> - Detectar e agrupar stack traces Python, Java e Go
> - Agrupar entradas por `template_id`
>
> Use constantes nomeadas: `_SPIKE_WINDOW_SECONDS = 60`, `_SPIKE_THRESHOLD = 10`, `_MIN_ENTRIES_FOR_ANALYSIS = 2`.

**Resultado:**
- Criado `src/analyzer/detector.py` com `AnomalyDetector`
- Funções auxiliares privadas: `_compute_severity_distribution`, `_detect_spikes`, `_extract_stack_traces`
- Regex para detecção de stack traces Python, Java e Go

---

## Prompt 3 — Implementar detecção de spikes com janela deslizante

**Prompt:**
> A função `_detect_spikes` deve usar janela deslizante de 60 segundos. Para cada posição `i` na lista de erros ordenada por timestamp, colete todas as entradas dentro de `[timestamp[i], timestamp[i] + 60s]`. Se houver ≥10 entradas na janela, crie um `Spike` e avance o ponteiro para depois do fim da janela. O `Spike` deve ter `end_time > start_time` (se forem iguais, adicione 1 segundo).

**Decisões técnicas:**
- Filtra apenas entradas com `severity in {ERROR, CRITICAL}` e `timestamp is not None`
- Ordena por timestamp antes de aplicar a janela
- Avança `i` pelo tamanho da janela para evitar spikes sobrepostos
- Coleta `template_ids` únicos das entradas do spike

---

## Prompt 4 — Implementar agrupamento de stack traces

**Prompt:**
> A função `_extract_stack_traces` deve detectar e agrupar stack traces multi-linha. Use regex para identificar o início de cada tipo:
> - Python: `Traceback \(most recent call last\)`
> - Java: `Exception in thread|at\s+[\w\.$]+\([\w\.]+\.java:\d+\)`
> - Go: `panic:|goroutine\s+\d+\s+\[`
>
> Agrupe linhas de continuação até encontrar uma linha não relacionada. Descarte traces de linha única.

**Bug encontrado e corrigido:**
Durante os testes, foi identificado que o modelo `LogEntry` tem `str_strip_whitespace = True` (configurado via `model_config`), o que remove espaços iniciais de `raw_content`. A lógica de continuação de traceback Python verificava `raw.startswith("  ")` — que nunca seria verdadeiro após o strip.

**Correção aplicada em `detector.py`:**
```python
# Antes (bugado):
elif current_type == "python" and (
    raw.startswith("  ") or raw.startswith("\t") or "Error:" in raw
):

# Depois (corrigido):
elif current_type == "python" and (
    raw.startswith("  ")
    or raw.startswith("\t")
    or raw.startswith("File ")
    or "Error:" in raw
    or "Exception:" in raw
    or "Warning:" in raw
):
```

---

## Prompt 5 — Escrever testes unitários abrangentes

**Prompt:**
> Escreva testes unitários em `tests/analyzer/test_detector.py` cobrindo todos os critérios de aceitação da Tarefa 5:
> - Interface abstrata não pode ser instanciada
> - Agrupamento por `template_id`
> - Distribuição de severidade soma 100% das entradas
> - Spike com exatamente 10 erros em 60s
> - Spike com 15 erros em 60s
> - Sem spike com 9 erros em 60s
> - Sem spike com 10 erros em 61s
> - Python traceback multi-linha agrupado em 1 evento
> - Java stacktrace multi-linha agrupado em 1 evento
> - Go panic multi-linha agrupado em 1 evento
> - `insufficient_data=True` para 0 e 1 entradas
> - Casos: 0, 1, 2, 10, 100 entradas

**Resultado:**
- 45 testes unitários organizados em 7 classes
- Helper `make_entry()` para criação de `LogEntry` nos testes
- Helper `make_error_entries_in_window()` para cenários de spike

---

## Prompt 6 — Adicionar property-based tests com Hypothesis

**Prompt:**
> Adicione testes de propriedade usando `hypothesis` para validar invariantes do `AnomalyDetector`:
> 1. A distribuição de severidade sempre soma igual a `total_entries` (para qualquer combinação de severidades)
> 2. `insufficient_data=True` sempre que há < 2 entradas (para n=0 e n=1)
> 3. Todo spike detectado tem `error_count >= 10` (para qualquer número de erros ≥10 na janela)
>
> Anote cada teste com `**Validates: Requirements RF-04.X**`.

**Resultado:**
- 4 property-based tests com `@given` e `@settings`
- Estratégias customizadas para gerar entradas válidas
- Todos os testes passam com 20-50 exemplos gerados

---

## Resultado Final

- **49 novos testes** em `tests/analyzer/test_detector.py`
- **190 testes totais** passando (141 existentes + 49 novos)
- **1 bug corrigido** em `src/analyzer/detector.py` (continuação de traceback Python com `raw_content` stripped)
- Cobertura de todos os critérios de aceitação da Tarefa 5
