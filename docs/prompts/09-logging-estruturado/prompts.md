# Prompts — Configurar Logging Estruturado

## Tarefa

Configurar sistema de logging estruturado com structlog para o LogPulse IA, conforme RNF-05 e padrões definidos na documentação técnica.

---

## Prompt 1 — Implementação do módulo de logging

```
Configurar logging com formato estruturado.
Tarefa Principal: #297
Descrição: Configurar sistema de logging estruturado
Critérios de Aceitação: RNF-05
Estimativa: 1h
Requisitos: RNF-05

Implemente a tarefa, crie a branch e commite conforme estabelecido em .github,
documente os prompts utilizados para a construção da tarefa em docs/prompts e faça o push.
```

### Resultado

O Kiro analisou o projeto existente e implementou:

1. **`src/core/__init__.py`** — Módulo core com exports públicos (`configure_logging`, `get_logger`)
2. **`src/core/logging.py`** — Configuração completa de logging estruturado com:
   - `configure_logging()`: Configura structlog globalmente com suporte a JSON e texto legível
   - `get_logger()`: Retorna logger bound com contexto opcional
   - Resolução de nível via parâmetro, variável de ambiente `LOGPULSE_LOG_LEVEL` ou default INFO
   - Resolução de formato via parâmetro, variável `LOGPULSE_LOG_FORMAT` ou auto-detecção (JSON em CI/container, texto em terminal)
   - Integração com stdlib logging para capturar logs de bibliotecas terceiras (uvicorn, httpx)
3. **`tests/core/__init__.py`** — Pacote de testes do módulo core
4. **`tests/core/test_logging.py`** — 27 testes unitários cobrindo:
   - Resolução de nível de log (10 testes)
   - Resolução de formato de saída (7 testes)
   - Configuração global (4 testes)
   - Criação e uso de loggers (6 testes)
5. **`pyproject.toml`** — Adicionada dependência `structlog~=24.1.0`

### Variáveis de Ambiente Suportadas

| Variável              | Valores                  | Default |
|-----------------------|--------------------------|---------|
| `LOGPULSE_LOG_LEVEL`  | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO    |
| `LOGPULSE_LOG_FORMAT` | json, text               | auto    |

### Uso

```python
from src.core.logging import configure_logging, get_logger

# Na inicialização da aplicação (ex: startup FastAPI)
configure_logging()

# Em qualquer módulo
logger = get_logger(__name__)
logger.info("analysis_started", source="app.log", entries_count=150)
logger.warning("line_parse_failed", line_number=42)
logger.error("ai_engine_failed", error="timeout", model="llama3")
```
