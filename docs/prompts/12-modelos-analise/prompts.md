# Prompts — Tarefa #259: Criar Modelos de Análise (Spike, AnalysisResult)

## Contexto

Criar modelos Pydantic para representar resultados da análise de anomalias.
Requisitos RF-04.2 (detecção de anomalias) e RF-04.4 (distribuição de severidade).

## Prompt Utilizado

```
Criar modelos Pydantic em src/models/schemas.py para análise de anomalias:

1. Spike:
   - start_time: datetime (início da janela)
   - end_time: datetime (fim da janela, deve ser > start_time)
   - error_count: int (mínimo 10)
   - template_ids: List[str] (default vazio)
   - Validação: end_time > start_time

2. AnalysisResult:
   - total_entries: int (>= 0)
   - severity_distribution: Dict[SeverityLevel, int]
   - error_count: int (>= 0, soma de ERROR + CRITICAL)
   - warning_count: int (>= 0)
   - spikes: List[Spike]
   - stack_traces: List[str]
   - templates: List[LogTemplate]
   - insufficient_data: bool (True se < 2 entradas)

Testes de propriedade validando:
- Spike com end > start e count >= 10 é sempre válido
- error_count < 10 é sempre rejeitado
- Contadores negativos são rejeitados
- Serialização JSON roundtrip funciona
```

## Resultado

- `src/models/schemas.py` — Modelos Spike e AnalysisResult com validações Pydantic
- `tests/models/test_analysis_models.py` — 27 testes (21 unitários + 6 property-based)
- Requisitos RF-04.2 e RF-04.4 atendidos
