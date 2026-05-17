# Criação de Tarefas no Kanban via GitHub CLI

Guia para criar issues no projeto LogPulse IA usando GitHub CLI.

---

## Pré-requisitos

- GitHub CLI instalado: `gh --version`
- Autenticação: `gh auth login`
- Projeto Kanban: **LogPulse AI** (número 7)

---

## Comandos Principais

### 1. Criar Issue

```bash
gh issue create \
  --title "Título da tarefa" \
  --body "Descrição em Markdown" \
  --label "enhancement"
```

### 2. Adicionar ao Kanban

```bash
gh project item-add 7 \
  --owner IA-para-DEVs-SCTEC-T2 \
  --url <URL_DA_ISSUE>
```

---

## Template de Issue

```markdown
## [Título]

**Spec:** logpulse-ia

## Descrição
[Descrição detalhada]

## Critérios de Aceitação
- [Critério 1]
- [Critério 2]

## Dependências
[Tarefa X] ou Nenhuma

## Estimativa
[X horas]
```

---

## Scripts Automatizados

**Windows:**
```powershell
.\create-test-task.ps1
```

**Linux/Mac:**
```bash
./create-test-task.sh
```

---

## Comandos Úteis

```bash
# Listar issues
gh issue list

# Ver detalhes
gh issue view <NÚMERO>

# Editar
gh issue edit <NÚMERO> --title "Novo título"

# Fechar/Reabrir
gh issue close <NÚMERO>
gh issue reopen <NÚMERO>
```

---

## Labels Disponíveis

- `enhancement` - Novas funcionalidades
- `bug` - Correção de bugs
- `documentation` - Documentação
- `test` - Testes

---

## Solicitação ao Assistente

**Formato básico:**
```
Criar tarefa no kanban:
- Título: [título]
- Descrição: [descrição]
- Dependências: [dependências ou "Nenhuma"]
- Estimativa: [X horas]
```

**Exemplo:**
```
Criar tarefa: Implementar validação de entrada
Descrição: Validar dados nos endpoints da API
Dependências: Nenhuma
Estimativa: 2 horas
```

---

## Troubleshooting

**Label não encontrada:** Use `enhancement` ou crie via interface web

**Erro de autenticação:** Execute `gh auth login`

**Assignee inválido:** Use `--assignee "@me"` ou remova o parâmetro

---

**Referências:** [GitHub CLI Manual](https://cli.github.com/manual/)
