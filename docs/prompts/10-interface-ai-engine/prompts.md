# Prompts — Tarefa #273: Criar Interface Abstrata AIEngine

## Contexto

Definir contrato abstrato para implementações de AI engine, garantindo que
qualquer provedor de LLM (Ollama, OpenAI, Gemini) possa ser integrado
respeitando o mesmo contrato.

## Prompt Utilizado

```
Definir interface abstrata AIEngine em src/ai/base.py com:
- Classe abstrata herdando de ABC
- Método abstrato `diagnose(analysis: AnalysisResult, sample_entries: List[LogEntry]) -> AIDiagnosis`
- Docstrings em português documentando o contrato
- Exceções documentadas: AIEngineTimeoutError, AIEngineUnavailableError
- Testes unitários validando que:
  - AIEngine não pode ser instanciado diretamente
  - Subclasse sem implementar diagnose lança TypeError
  - Subclasse concreta pode ser instanciada e retorna AIDiagnosis
  - diagnose é marcado como abstractmethod
```

## Resultado

- `src/ai/base.py` — Interface abstrata AIEngine com contrato documentado
- `tests/ai/test_base.py` — Testes unitários dedicados para o contrato abstrato
- Requisito RF-05.1 atendido
