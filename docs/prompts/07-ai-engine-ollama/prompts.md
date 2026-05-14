# Prompts — AIEngine com Ollama (Task 6)

## Contexto

Esta tarefa implementa o componente `AIEngine` responsável por gerar diagnósticos inteligentes a partir da análise de logs, utilizando o Ollama/LLaMA 3 como backend de LLM via OpenAI SDK (drop-in replacement).

---

## Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `src/exceptions.py` | Hierarquia de exceções customizadas do LogPulse IA |
| `src/ai/__init__.py` | Exportações públicas do módulo AI |
| `src/ai/base.py` | Interface abstrata `AIEngine` com ABC |
| `src/ai/ollama_engine.py` | Implementação `OllamaAIEngine` com Ollama/LLaMA 3 |
| `tests/ai/__init__.py` | Pacote de testes do módulo AI |
| `tests/ai/test_ollama_engine.py` | Testes abrangentes com mocks do Ollama |

---

## Decisões de Design

### 1. Interface Abstrata com ABC

A classe `AIEngine` usa `ABC` (Abstract Base Class) para garantir que implementações concretas respeitem o contrato do método `diagnose`. Isso permite trocar o provedor de LLM no futuro sem alterar o código cliente.

```python
class AIEngine(ABC):
    @abstractmethod
    def diagnose(
        self,
        analysis: AnalysisResult,
        sample_entries: List[LogEntry],
    ) -> AIDiagnosis: ...
```

### 2. Amostragem Estratificada

Para respeitar o requisito RNF-04 (enviar apenas amostras ao LLM, nunca o log completo), implementamos amostragem estratificada com proporções fixas:

- **70%** de erros (ERROR + CRITICAL) — foco nos problemas críticos
- **20%** de warnings — contexto de degradação
- **10%** de outros (INFO, DEBUG) — contexto geral
- **Máximo de 50 entradas** — limita o tamanho do prompt

### 3. Verificação de Disponibilidade

Antes de qualquer chamada ao LLM, o engine verifica se o Ollama está acessível via conexão TCP na porta 11434. Isso evita timeouts desnecessários e fornece mensagem de erro clara ao usuário.

### 4. Retry com Backoff Exponencial

Implementado com 3 tentativas e delays de 1s, 2s, 4s entre elas. Captura `APITimeoutError` e `APIConnectionError` do SDK OpenAI. Após esgotar as tentativas, lança `AIEngineTimeoutError`.

### 5. Validação de Resposta via Pydantic

A resposta do LLM é parseada como JSON e validada pelo schema `AIDiagnosis` do Pydantic, que garante:
- Mínimo de 3 hipóteses (`min_length=3`)
- Campo `action` não vazio em cada hipótese
- Campo `probability` com valores válidos ("alta", "média", "baixa")

---

## Prompt do Sistema

O prompt do sistema instrui o LLM a:
1. Responder **apenas** com JSON válido (sem texto adicional)
2. Seguir o schema `AIDiagnosis` exatamente
3. Gerar **exatamente 3 ou mais hipóteses** ordenadas por probabilidade
4. Incluir **ação concreta** em cada hipótese
5. Basear-se **apenas** nas informações fornecidas (sem inventar dados)

---

## Hierarquia de Exceções

```
LogPulseError
├── AIEngineError
│   ├── AIEngineTimeoutError    # Timeout após 3 tentativas
│   └── AIEngineUnavailableError # Ollama indisponível
├── ParsingError
├── AnalysisError
└── StorageError
```

---

## Testes Implementados (26 testes)

### Interface Abstrata (3 testes)
- `AIEngine` não pode ser instanciado diretamente
- `OllamaAIEngine` é subclasse de `AIEngine`
- Subclasse sem `diagnose` lança `TypeError`

### Amostragem Estratificada (8 testes)
- Lista vazia retorna lista vazia
- Menos de 50 entradas retorna todas
- Amostragem limita a 50 entradas
- ~70% de erros na amostra
- ~20% de warnings na amostra
- ~10% de outros na amostra
- Funciona com apenas erros
- Retorna exatamente `max_entries` quando há suficientes

### Disponibilidade do Ollama (3 testes)
- `AIEngineUnavailableError` quando Ollama está indisponível
- Prossegue para chamada quando disponível
- Mensagem de erro contém "ollama serve"

### Timeout e Retry (4 testes)
- `AIEngineTimeoutError` após 3 tentativas
- Cliente chamado exatamente 3 vezes
- Delays corretos: 1s, 2s (backoff exponencial)
- `APIConnectionError` também aciona retry

### Parsing e Validação (6 testes)
- Resposta válida parseada para `AIDiagnosis`
- Diagnóstico tem pelo menos 3 hipóteses
- Menos de 3 hipóteses lança `ValidationError`
- `action` vazio lança `ValidationError`
- Bloco markdown é removido antes do parse
- Cada hipótese tem `action` não vazio

### Integração (2 testes)
- `diagnose` funciona com entradas de amostra reais
- Sucesso na segunda tentativa após falha na primeira

---

## Prompt Utilizado para Geração

```
Implementar AIEngine com Ollama (Task 6) para o projeto LogPulse IA.

Criar:
1. src/exceptions.py — hierarquia de exceções customizadas
2. src/ai/base.py — interface abstrata AIEngine com ABC
3. src/ai/ollama_engine.py — OllamaAIEngine com:
   - Cliente OpenAI SDK → http://localhost:11434/v1
   - Amostragem estratificada (70% erros, 20% warnings, 10% outros, máx 50)
   - Prompt do sistema para análise de logs
   - Chamada com modelo llama3
   - Timeout 30s + retry backoff exponencial (1s, 2s, 4s)
   - Verificação de disponibilidade via socket TCP
   - Validação de resposta com Pydantic AIDiagnosis
4. tests/ai/test_ollama_engine.py — 26 testes com unittest.mock
```
