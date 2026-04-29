# Git Hooks Locais — LogPulse IA

Este diretório contém **Git Hooks** que validam commits e branches **localmente**, antes de enviar ao GitHub.

## 🎯 O Que São Git Hooks?

Git Hooks são scripts que o Git executa automaticamente em momentos específicos:

- **commit-msg**: Executado ao fazer `git commit` (valida a mensagem)
- **pre-push**: Executado ao fazer `git push` (valida o nome da branch)

## 🔒 Diferença: Validações Locais vs GitHub Actions

### Validações Locais (Git Hooks)
```
git commit -m "teste: ..."  ❌ BLOQUEADO IMEDIATAMENTE
                            ↓
                    Mensagem de erro
                    Commit não é criado
```

### Validações no GitHub (GitHub Actions)
```
git commit -m "teste: ..."  ✅ Aceito localmente
git push                    ✅ Aceito localmente
                            ↓
                    Pull Request criado
                            ↓
                    GitHub Actions executa
                            ↓
                    ❌ Validações falham
                    🔒 Merge bloqueado
```

## 🚀 Como Ativar

### Windows (PowerShell)

```powershell
.\\.githooks\\setup.ps1
```

### Linux/macOS (Bash)

```bash
chmod +x .githooks/setup.sh
./.githooks/setup.sh
```

### Manual

```bash
git config core.hooksPath .githooks
```

## ✅ Hooks Disponíveis

### 1. `commit-msg`

Valida a mensagem de commit **antes** de criar o commit.

**Bloqueia:**
- ❌ `teste: adiciona feature`
- ❌ `ajustes`
- ❌ `WIP`
- ❌ `feature: nova funcionalidade`

**Permite:**
- ✅ `feat: adiciona parser de logs`
- ✅ `fix: corrige timeout`
- ✅ `docs: atualiza README`
- ✅ `refactor: simplifica analyzer`

### 2. `pre-push`

Valida o nome da branch **antes** de fazer push.

**Bloqueia:**
- ❌ `teste-validacao`
- ❌ `feat/nova-feature`
- ❌ `ajustes`
- ❌ `feature-AB` (muito curto)

**Permite:**
- ✅ `main`
- ✅ `develop`
- ✅ `feature-analise-logs`
- ✅ `hotfix-correcao-timeout`

## 🧪 Testando os Hooks

### Teste 1: Commit Inválido

```bash
git commit -m "teste: mensagem inválida"
```

**Resultado esperado:**
```
❌ ERRO: Mensagem de commit inválida!
[Mensagem de erro detalhada]
```

### Teste 2: Branch Inválida

```bash
git checkout -b teste-branch
git push origin teste-branch
```

**Resultado esperado:**
```
❌ ERRO: Nome da branch inválido!
[Mensagem de erro detalhada]
```

### Teste 3: Commit e Branch Válidos

```bash
git checkout -b feature-nova-funcionalidade
git commit -m "feat: adiciona nova funcionalidade"
git push origin feature-nova-funcionalidade
```

**Resultado esperado:**
```
✅ Mensagem de commit válida!
✅ Nome da branch válido!
[Push realizado com sucesso]
```

## 🔧 Desativando os Hooks

Se precisar desativar temporariamente:

```bash
# Desativar permanentemente
git config --unset core.hooksPath

# Ou pular hooks em um commit específico
git commit --no-verify -m "mensagem"

# Ou pular hooks em um push específico
git push --no-verify
```

⚠️ **Atenção:** Mesmo pulando os hooks locais, as validações do GitHub Actions ainda serão executadas!

## 📊 Comparação Completa

| Aspecto                  | Git Hooks (Local)           | GitHub Actions (Remoto)     |
|--------------------------|-----------------------------|-----------------------------|
| **Quando executa**       | Antes de commit/push        | Após criar Pull Request     |
| **Onde executa**         | Na sua máquina              | Servidor do GitHub          |
| **Pode ser pulado**      | Sim (--no-verify)           | Não (obrigatório)           |
| **Feedback**             | Imediato                    | Após alguns segundos        |
| **Configuração**         | Por desenvolvedor           | Centralizada no repositório |
| **Vantagem**             | Feedback instantâneo        | Não pode ser contornado     |

## 💡 Recomendação

**Use ambos!**

1. **Git Hooks locais**: Feedback rápido durante o desenvolvimento
2. **GitHub Actions**: Garantia final antes do merge

Isso cria uma **defesa em camadas**:
```
Desenvolvedor → Git Hooks → Push → GitHub Actions → Merge
               ✅ Valida    ✅ Envia  ✅ Valida      ✅ Protege
```

## 🆘 Problemas Comuns

### "permission denied" (Linux/macOS)

**Solução:**
```bash
chmod +x .githooks/commit-msg
chmod +x .githooks/pre-push
```

### Hooks não estão executando

**Solução:**
```bash
# Verificar configuração
git config core.hooksPath

# Deve retornar: .githooks
# Se não retornar nada, execute:
git config core.hooksPath .githooks
```

### Quero pular a validação uma vez

**Solução:**
```bash
# Pular validação de commit
git commit --no-verify -m "mensagem"

# Pular validação de push
git push --no-verify
```

## 📚 Referências

- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**🎉 Com os Git Hooks ativados, você terá feedback instantâneo sobre problemas de formatação!**
