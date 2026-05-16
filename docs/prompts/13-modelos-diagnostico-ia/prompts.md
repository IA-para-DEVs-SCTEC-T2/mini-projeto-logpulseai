# Prompts — Tarefa #259: Criar Modelos de Diagnóstico IA (Hypothesis, AIDiagnosis)

## Contexto

Criar modelos Pydantic para representar diagnóstico gerado pela IA.
Requisitos RF-05.2 (diagnóstico com causa raiz) e RF-05.3 (hipóteses ordenadas).

## Prompt Utilizado

```
Criar modelos Pydantic em src/models/schemas.py para diagnóstico IA:

1. Hypothesis:
   - description: str (não vazio)
   - probability: str (apenas 'alta', 'média' ou 'baixa', case-insensitive)
   - action: str (não vazio, não apenas espaços)
   - related_line: Optional[int] (linha do código relacionada)
   - Validação: probability normalizada para lowercase

2. AIDiagnosis:
   - summary: str (não vazio)
   - probable_cause: str (não vazio)
   - hypotheses: List[Hypothesis] (mínimo 3)
   - suggested_fix: str (default vazio)
   - confidence: float (0.0 a 1.0, default 0.0)
   - Validação: mínimo 3 hipóteses, confidence no range

Testes de propriedade validando:
- Probabilidades válidas sempre aceitas
- Probabilidades inválidas sempre rejeitadas
- confidence entre 0 e 1 sempre aceito
- confidence > 1 sempre rejeitado
- 3+ hipóteses sempre aceitas
- <3 hipóteses sempre rejeitadas
- Serialização JSON roundtrip funciona
```

## Resultado

- `src/models/schemas.py` — Modelos Hypothesis e AIDiagnosis com validações Pydantic
- `tests/models/test_diagnosis_models.py` — 39 testes (32 unitários + 7 property-based)
- Requisitos RF-05.2 e RF-05.3 atendidos
