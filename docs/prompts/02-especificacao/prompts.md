# Prompts — Etapa 02: Especificação

Prompts utilizados durante a criação do `requirements.md`.

---

## P02-01 — Criação da estrutura do requirements.md

**Data:** 2025-05-04
**Ferramenta:** Kiro

**Prompt:**
```
Descrição: Criar a estrutura do arquivo requirements.md para documentar os requisitos
do sistema de forma padronizada, clara e organizada.

Requisitos:
- Criar arquivo requirements.md no repositório (local: .kiro/specs/logpulse-ia)
- Definir estrutura padrão: Introdução, Visão geral, Requisitos funcionais,
  Requisitos não funcionais, Regras de negócio, Entradas e saídas
- Padronizar escrita dos requisitos com linguagem clara e objetiva
- Cada requisito deve ser descrito de forma independente

minha tarefa é a de criar Criar Estrutura Spec - requirements.md
```

**Resultado:**
Arquivo criado com estrutura numerada, glossário, 9 requisitos funcionais (RF-01 a RF-09) com critérios de aceitação no padrão `WHEN/IF/THEN/SHALL`, requisitos não funcionais, regras de negócio e tabelas de entradas/saídas.

---

## P02-02 — Ajuste de escopo para MVP com FastAPI

**Data:** 2025-05-04
**Ferramenta:** Kiro

**Prompt:**
```
sobre os critérios de aceitação: no MVP somente oferecemos ao usuário a FASTApi,
onde ele faz manualmente o upload do arquivo de log, ou cola em campo de texto o
trecho que log que quer a análise. O MVP não oferecerá automatização para busca em
repositório, integração com Kubernates ou qualquer outra, isso entra no roadmap
para uma nova versão.
```

**Resultado:**
Removidos requisitos de CLI, stdin/pipe e `--follow`. Adicionados endpoints `POST /analyze/upload` e `POST /analyze/text` com limites de tamanho. Criada seção de Roadmap com itens fora do MVP.

---

## P02-03 — Realinhamento com steering files (IA nativa, Ollama, SQLite)

**Data:** 2025-05-04
**Ferramenta:** Kiro

**Prompt:**
```
pensamos no uso de IA nativo, voce analisou os steering antes de montar o requirements?
```

**Resultado:**
Releitura dos steering files revelou divergências. Requirements reescrito com: Ollama + LLaMA 3 como IA nativa, OpenAI SDK como drop-in replacement, SQLite para persistência, Drain3 para parsing, endpoints corretos (`api/v1/logs/...`), AIEngine sempre acionado, cobertura mínima de 30% e validação via Pydantic.
