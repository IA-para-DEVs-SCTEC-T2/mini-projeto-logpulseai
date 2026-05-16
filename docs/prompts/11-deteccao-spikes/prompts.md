# Prompts — Tarefa #269: Implementar Detecção de Spikes

## Contexto

Detectar spikes de erros usando janela deslizante de 60 segundos.
Requisitos RF-04.2 (detecção de anomalias) e RN-02 (regras de negócio).

## Prompt Utilizado

```
Implementar detecção de spikes de erro no AnomalyDetector com:
- Janela deslizante de 60 segundos
- Threshold de ≥10 erros (ERROR ou CRITICAL) para caracterizar spike
- Coleta de template_ids das entradas envolvidas
- Entradas sem timestamp são ignoradas
- Spikes não se sobrepõem (avança para depois do fim da janela)

Testes de propriedade (hypothesis) validando:
- ≥10 erros em ≤60s sempre gera spike
- <10 erros nunca gera spike
- INFO/WARNING/DEBUG nunca geram spike
- Todo spike tem error_count >= 10
- start_time < end_time em todo spike
- Duração do spike ≤ 61s (janela + margem)

Testes determinísticos para casos de borda:
- Todos os erros no mesmo timestamp
- Dois bursts separados geram 2 spikes
- Entradas sem timestamp ignoradas
- Lista vazia retorna vazio
```

## Resultado

- `src/analyzer/detector.py` — Implementação da função `_detect_spikes` com janela deslizante
- `tests/analyzer/test_spike_detection.py` — 16 testes (7 property-based + 7 edge cases + 2 integração)
- Requisitos RF-04.2 e RN-02 atendidos
