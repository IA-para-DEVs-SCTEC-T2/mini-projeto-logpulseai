# Validações no GitHub — LogPulse IA

## 🎯 Como Funcionam as Validações no GitHub

As validações no GitHub são executadas através de **GitHub Actions** e acontecem **automaticamente** quando você cria ou atualiza um Pull Request.

## 📁 Workflows Configurados

### 1. Validação de Nome de Branch
**Arquivo:** `.github/workflows/branch-validation.yml`

**Quando executa:**
- Ao abrir um Pull Request
- Ao fazer push de novos commits em um PR existente

**O que valida:**
- Nome da branch deve seguir o padrão: `feature-<nome>` ou `hotfix-<nome>`
- Branches protegidas `main` e `develop` são permitidas
- Nome deve ter mínimo 3 caracteres após o prefixo
- Apenas letras minúsculas, números e hífens

### 2. Validação de Mensagens de Commit
**Arquivo:** `.github/workflows/commit-validation.yml`

**Quando executa:**
- Ao abrir um Pull Request
- Ao fazer push de novos commits em um PR existente

**O que valida:**
- Todos os commits do PR devem seguir o padrão Conventional Commits
- Prefixos permitidos: `feat:`, `fix:`, `docs:`, `refactor:`
- Formato: `<tipo>: <descrição>` ou `<tipo>(escopo): <descrição>`

---

## 🧪 Como Testar as Validações

### Teste 1: Branch Válida com Commit Válido ✅

```bash
# 1. Criar branch válida
git checkout main
git checkout -b feature-teste-validacoes

# 2. Fazer commit válido
git commit --allow-empty -m "feat: testa validações do GitHub"

# 3. Push
git push -u origin feature-teste-validacoes

# 4. Criar Pull Request
gh pr create \
  --title "feat: testa validações do GitHub" \
  --body "PR de teste para validar os workflows do GitHub Actions" \
  --base main
```

**Resultado esperado:**
- ✅ Workflow "Branch Naming Rules" - PASSA
- ✅ Workflow "Commit Message Validation" - PASSA
- ✅ Merge permitido (após 2 aprovações)

---

### Teste 2: Branch Inválida ❌

```bash
# 1. Criar branch inválida
git checkout main
git checkout -b teste-branch-invalida

# 2. Fazer commit válido
git commit --allow-empty -m "feat: teste com branch inválida"

# 3. Push
git push -u origin teste-branch-invalida

# 4. Criar Pull Request
gh pr create \
  --title "feat: teste com branch inválida" \
  --body "Este PR deve falhar na validação de branch" \
  --base main
```

**Resultado esperado:**
- ❌ Workflow "Branch Naming Rules" - FALHA
- ✅ Workflow "Commit Message Validation" - PASSA
- 🔒 Merge bloqueado

**Mensagem de erro:**
```
❌ ERRO: Nome da branch inválido!

Branch atual: teste-branch-invalida

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 PADRÃO ACEITO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  feature-<nome-da-tarefa>
  hotfix-<nome-da-tarefa>
  main
  develop
```

---

### Teste 3: Commit Inválido ❌

```bash
# 1. Criar branch válida
git checkout main
git checkout -b feature-teste-commit-invalido

# 2. Fazer commit inválido
git commit --allow-empty -m "adicionando funcionalidade"

# 3. Push
git push -u origin feature-teste-commit-invalido

# 4. Criar Pull Request
gh pr create \
  --title "teste: commit inválido" \
  --body "Este PR deve falhar na validação de commit" \
  --base main
```

**Resultado esperado:**
- ✅ Workflow "Branch Naming Rules" - PASSA
- ❌ Workflow "Commit Message Validation" - FALHA
- 🔒 Merge bloqueado

**Mensagem de erro:**
```
❌ ERRO: Commits com formato inválido detectados!

Os seguintes commits não seguem o padrão de Conventional Commits:

  ❌ adicionando funcionalidade

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ TIPOS PERMITIDOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • feat:     Nova funcionalidade
  • fix:      Correção de bug
  • docs:     Documentação
  • refactor: Melhoria sem mudar função
```

---

## 🔍 Visualizando as Validações no GitHub

### Passo 1: Criar Pull Request

Após criar o PR, você verá na página do Pull Request:

```
┌─────────────────────────────────────────────────────────────┐
│  Pull Request #1                                            │
│  feat: adiciona validações                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏳ Some checks haven't completed yet                       │
│                                                             │
│  ⏳ Branch Naming Rules — In progress                       │
│  ⏳ Commit Message Validation — In progress                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Passo 2: Aguardar Execução (5-10 segundos)

Os workflows serão executados automaticamente.

### Passo 3: Ver Resultados

**Se tudo estiver correto:**
```
┌─────────────────────────────────────────────────────────────┐
│  Pull Request #1                                            │
│  feat: adiciona validações                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ All checks have passed                                  │
│                                                             │
│  ✅ Branch Naming Rules — Passed                            │
│  ✅ Commit Message Validation — Passed                      │
│                                                             │
│  ⚠️  This branch requires 2 approving reviews               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Se houver erro:**
```
┌─────────────────────────────────────────────────────────────┐
│  Pull Request #1                                            │
│  teste: branch inválida                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ❌ Some checks were not successful                         │
│                                                             │
│  ❌ Branch Naming Rules — Failed                            │
│  ✅ Commit Message Validation — Passed                      │
│                                                             │
│  🔒 Merging is blocked                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Onde Ver os Logs Detalhados

### Opção 1: Via Interface do GitHub

1. Acesse o Pull Request
2. Clique na aba **"Checks"** ou **"Actions"**
3. Clique no workflow que falhou
4. Veja os logs completos com as mensagens de erro

### Opção 2: Via GitHub CLI

```bash
# Listar workflows do último PR
gh pr checks

# Ver detalhes de um workflow específico
gh run view <run-id>
```

---

## 🧹 Testando com as Branches Existentes

Você já tem branches no repositório que podem ser usadas para testar:

### Teste com Branch Válida

```bash
# Criar PR da branch válida
gh pr create \
  --head feature-adiciona-git-hooks \
  --title "feat: adiciona git hooks para validação local" \
  --body "Implementa validações locais via Git Hooks" \
  --base main
```

**Resultado esperado:** ✅ Todas as validações passam

### Teste com Branch Inválida

```bash
# Criar PR da branch inválida
gh pr create \
  --head teste-validacao \
  --title "teste: validações" \
  --body "Este PR deve falhar nas validações" \
  --base main
```

**Resultado esperado:** ❌ Validações falham

---

## 🔧 Como Corrigir Erros

### Se a Branch Estiver Inválida

```bash
# Renomear a branch localmente
git branch -m feature-nome-correto

# Deletar a branch antiga no remoto
git push origin --delete nome-antigo

# Push da branch renomeada
git push -u origin feature-nome-correto

# Fechar o PR antigo e criar um novo
gh pr close <numero-pr-antigo>
gh pr create --head feature-nome-correto --base main
```

### Se o Commit Estiver Inválido

```bash
# Corrigir o último commit
git commit --amend -m "feat: mensagem correta"

# Force push (cuidado!)
git push --force-with-lease

# O PR será atualizado automaticamente e as validações rodarão novamente
```

---

## 📋 Checklist de Validações

Antes de criar um Pull Request, verifique:

- [ ] Nome da branch segue o padrão `feature-<nome>` ou `hotfix-<nome>`
- [ ] Todos os commits seguem o padrão `<tipo>: <descrição>`
- [ ] Tipos de commit são: `feat:`, `fix:`, `docs:` ou `refactor:`
- [ ] Git Hooks locais estão ativados (feedback instantâneo)
- [ ] Código está funcionando e testado

---

## 🎯 Fluxo Completo

```
1. Desenvolvedor cria branch válida
   git checkout -b feature-nova-funcionalidade
   
2. Git Hook valida localmente ✅
   
3. Desenvolvedor faz commit válido
   git commit -m "feat: adiciona funcionalidade"
   
4. Git Hook valida localmente ✅
   
5. Desenvolvedor faz push
   git push -u origin feature-nova-funcionalidade
   
6. Git Hook valida localmente ✅
   
7. Desenvolvedor cria Pull Request
   gh pr create --base main
   
8. GitHub Actions executa workflows
   ✅ Branch Naming Rules
   ✅ Commit Message Validation
   
9. Aguarda 2 aprovações
   👤 Revisor 1 aprova
   👤 Revisor 2 aprova
   
10. Merge permitido! 🎉
```

---

## 🆘 Problemas Comuns

### "Workflow não está executando"

**Causa:** Workflows só executam em Pull Requests, não em pushes diretos.

**Solução:** Crie um Pull Request para ver as validações.

### "Checks não aparecem no PR"

**Causa:** Pode levar alguns segundos para os workflows iniciarem.

**Solução:** Aguarde 10-30 segundos e recarregue a página.

### "Workflow falhou mas não sei por quê"

**Causa:** Precisa ver os logs detalhados.

**Solução:** 
1. Clique na aba "Checks" no PR
2. Clique no workflow que falhou
3. Leia os logs completos

---

## 📚 Referências

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)

---

**🎉 As validações do GitHub já estão configuradas e prontas para uso!**

Basta criar um Pull Request para vê-las em ação.
