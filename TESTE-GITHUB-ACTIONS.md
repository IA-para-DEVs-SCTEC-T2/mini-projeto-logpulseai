# 🧪 Guia Rápido: Testar Validações do GitHub

## ✅ As Validações Já Estão Configuradas!

Você já tem 2 workflows do GitHub Actions configurados:
- ✅ `.github/workflows/branch-validation.yml`
- ✅ `.github/workflows/commit-validation.yml`

Eles executam **automaticamente** quando você cria um Pull Request.

---

## 🚀 Teste Rápido (2 minutos)

### Opção 1: Testar com Branch Válida (deve passar ✅)

```bash
# Criar PR da branch que já existe
gh pr create \
  --head feature-adiciona-git-hooks \
  --title "feat: adiciona git hooks para validação local" \
  --body "Implementa validações locais via Git Hooks" \
  --base main
```

**Resultado esperado:**
- ✅ Branch Naming Rules → PASSA
- ✅ Commit Message Validation → PASSA
- ✅ Merge permitido (após 2 aprovações)

---

### Opção 2: Testar com Branch Inválida (deve falhar ❌)

```bash
# Criar PR da branch inválida que já existe
gh pr create \
  --head teste-validacao \
  --title "teste: validações" \
  --body "Este PR deve falhar nas validações" \
  --base main
```

**Resultado esperado:**
- ❌ Branch Naming Rules → FALHA
- ❌ Commit Message Validation → FALHA
- 🔒 Merge bloqueado

---

## 📱 Visualizar no GitHub

Após criar o PR, acesse:
```
https://github.com/IA-para-DEVs-SCTEC-T2/mini-projeto-logpulseai/pulls
```

Você verá:
1. ⏳ Workflows executando (5-10 segundos)
2. ✅ ou ❌ Resultado das validações
3. 🔒 Botão de merge bloqueado se houver falhas

---

## 🎯 O Que Acontece

```
Você cria PR
     ↓
GitHub Actions detecta
     ↓
Executa workflows automaticamente
     ↓
┌─────────────────────────────────┐
│ Branch Naming Rules             │
│ ✅ ou ❌                         │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ Commit Message Validation       │
│ ✅ ou ❌                         │
└─────────────────────────────────┘
     ↓
Se tudo ✅ → Aguarda 2 aprovações
Se algo ❌ → Merge bloqueado 🔒
```

---

## 📋 Resumo

| O Que | Onde | Quando |
|-------|------|--------|
| **Git Hooks** | Local (sua máquina) | Antes de commit/push |
| **GitHub Actions** | GitHub (servidor) | Ao criar/atualizar PR |
| **Branch Protection** | GitHub (servidor) | Ao tentar fazer merge |

**Todas as 3 camadas estão configuradas!** 🛡️

---

## 🔗 Links Úteis

- [Documentação Completa](docs/validacoes-github.md)
- [Workflow Git](docs/git-workflow.md)
- [Git Hooks](.githooks/README.md)

---

**🎉 Pronto! Crie um PR para ver as validações em ação!**
