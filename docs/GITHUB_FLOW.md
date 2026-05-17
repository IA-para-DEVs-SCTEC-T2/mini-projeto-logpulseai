# GitHub Flow - Guia Rápido

## Resumo

O LogPulse IA usa **GitHub Flow** simplificado com apenas 3 tipos de branches.

## Branches

| Branch | Propósito | Proteção |
|--------|-----------|----------|
| `main` | Código estável em produção | ✅ Protegida |
| `feature/*` | Novas funcionalidades | - |
| `bugfix/*` | Correções de bugs | - |

## Fluxo de Trabalho

```
┌─────────┐
│  main   │ ← sempre estável
└────┬────┘
     │
     ├─→ feature/nome ─→ PR (1 aprovação) ─→ merge ─→ main
     │
     └─→ bugfix/nome ─→ PR (1 aprovação) ─→ merge ─→ main
```

## Comandos Essenciais

### 1. Criar nova branch
```bash
git checkout main
git pull origin main
git checkout -b feature/minha-funcionalidade
# ou
git checkout -b bugfix/corrige-problema
```

### 2. Fazer commits semânticos
```bash
git add .
git commit -m "feat: adiciona parser syslog"
```

### 3. Abrir Pull Request
```bash
gh pr create \
  --title "feat: adiciona parser syslog" \
  --base main
```

### 4. Após merge, atualizar main
```bash
git checkout main
git pull origin main
```

## Commits Semânticos

### Formato
```
<tipo>: <descrição curta>
```

### Tipos Permitidos

| Tipo | Uso | Exemplo |
|------|-----|---------|
| `feat` | Nova funcionalidade | `feat: adiciona suporte a logs .gz` |
| `fix` | Correção de bug | `fix: corrige timeout na análise` |
| `docs` | Documentação | `docs: atualiza README` |
| `refactor` | Refatoração | `refactor: simplifica parser JSON` |

## Regras Importantes

### ✅ Permitido
- Criar branches `feature/*` e `bugfix/*` a partir de `main`
- Fazer commits semânticos
- Abrir PR para `main` com 1 aprovação mínima
- Deletar branch após merge

### ❌ Proibido
- Commit direto em `main`
- Branches sem prefixo `feature/` ou `bugfix/`
- Commits sem padrão semântico
- Aprovar seu próprio PR
- Merge sem aprovação

## Validações Automáticas

O projeto possui validações em CI/CD que verificam:

1. **Nome da branch** → deve ser `feature/*` ou `bugfix/*`
2. **Commits semânticos** → devem seguir o padrão `<tipo>: <descrição>`
3. **Aprovação obrigatória** → mínimo 1 aprovação para merge
4. **Proteção da main** → bloqueia commits diretos

## Exemplos Práticos

### Nova funcionalidade
```bash
git checkout main && git pull
git checkout -b feature/analise-logs-ia
git commit -m "feat: adiciona análise com IA"
gh pr create --title "feat: adiciona análise com IA" --base main
```

### Correção de bug
```bash
git checkout main && git pull
git checkout -b bugfix/correcao-parser-json
git commit -m "fix: corrige parsing de JSON malformado"
gh pr create --title "fix: corrige parsing de JSON malformado" --base main
```

## Dúvidas Frequentes

**Q: Posso usar `hotfix/` ao invés de `bugfix/`?**  
A: Não. Use apenas `bugfix/*` para correções.

**Q: Preciso de aprovação para fazer merge?**  
A: Sim, sempre 1 aprovação mínima de outro colaborador.

**Q: Posso commitar direto na `main`?**  
A: Não. Todo código entra via Pull Request.

**Q: E se eu precisar fazer uma mudança pequena na documentação?**  
A: Mesmo assim, crie uma branch `feature/atualiza-docs` e abra um PR.
