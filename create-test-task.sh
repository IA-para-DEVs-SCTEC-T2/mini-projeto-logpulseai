#!/bin/bash

# Script para criar tarefa de testes no GitHub via CLI

gh issue create \
  --title "Testes: Validar estrutura do projeto e dependências (Task 1)" \
  --body "## Testes: Validar estrutura do projeto e dependências

**Spec:** logpulse-ia

---

## Descrição

Criar testes automatizados para validar que a estrutura do projeto e todas as dependências estão corretamente configuradas conforme especificado na Task 1.

---

## Critérios de Aceitação

- Teste verifica existência de todas as pastas: \`src/\`, \`tests/\`, \`logs/\`, \`docs/\`
- Teste verifica subpastas em \`src/\`: \`ai/\`, \`api/\`, \`core/\`, \`models/\`, \`parsers/\`, \`services/\`
- Teste valida que \`pyproject.toml\` contém todas as dependências necessárias
- Teste valida que \`mypy --strict src/\` executa sem erros
- Teste valida que \`black --check src/\` executa sem erros
- Teste valida que \`isort --check-only src/\` executa sem erros
- Teste valida que \`ruff check src/\` executa sem erros
- Teste verifica que \`.env.example\` contém todas as variáveis documentadas
- Teste valida que \`pip install -e .\` executa sem erros

---

## Paralelismo e Dependências

[AVISO] Depende de: Tarefa 1 (estrutura do projeto) - CONCLUÍDA

---

## Estimativa

1-2 horas

---

## Requisitos

RNF-05, RNF-06, RNF-07

---

## Links Úteis

- [Ver tasks.md completo](.kiro/specs/logpulse-ia/tasks.md)
- [Ver requirements.md](.kiro/specs/logpulse-ia/requirements.md)
- [Ver design.md](.kiro/specs/logpulse-ia/design.md)

---

**Criado automaticamente via script**" \
  --label "test,enhancement" \
  --assignee @me

echo "✅ Issue de testes criada com sucesso!"
