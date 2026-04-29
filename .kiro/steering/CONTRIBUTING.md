---
inclusion: always
---

# Diretrizes de Contribuição — LogPulse IA

## Proteção da Branch `main`

- **Nunca** faça commits diretamente na branch `main`.
- Todo desenvolvimento deve ocorrer em branches separadas, criadas a partir de `main`.
- Alterações chegam à `main` exclusivamente via Pull Request (PR), após revisão e aprovação.

### Nomenclatura de branches

Use o padrão: `<tipo>/<descricao-curta>`

Exemplos:
- `feat/analise-logs-ia`
- `fix/correcao-parser-json`
- `chore/atualiza-dependencias`

---

## Commits Semânticos

> ⚠️ Commits semânticos padronizam o histórico do projeto.

Todos os commits devem seguir o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(escopo opcional): <descrição curta no imperativo>
```

### Tipos principais

| Tipo       | Quando usar                          |
|------------|--------------------------------------|
| `feat`     | Nova funcionalidade                  |
| `fix`      | Correção de bug                      |
| `docs`     | Documentação                         |
| `refactor` | Melhoria sem mudar função            |
| `style`    | Formatação, sem mudança de lógica    |
| `test`     | Adição ou correção de testes         |
| `chore`    | Manutenção (build, deps, configs)    |
| `perf`     | Melhoria de performance              |
| `ci`       | Mudanças em pipelines de CI/CD       |

### Exemplos reais

```bash
git commit -m "feat: adicionar login oauth"
git commit -m "fix: corrigir timeout"
git commit -m "docs: atualiza README com instruções de instalação"
git commit -m "refactor: simplifica parser de logs JSON"
```

### Exemplos inválidos ❌

```
ajustes
fix
WIP
corrigindo bug
```

---

## Pull Requests e Code Review

> ⚠️ Nunca aprove sua própria PR em projetos de equipe.

### Pull Request

Um PR é uma proposta formal de merge de uma branch. Boas práticas:

- **Título claro** seguindo o padrão semântico (ex: `feat: adiciona página de login`)
- **Descrição** explicando o que muda e o motivo
- **Prints** quando a alteração for visual

Exemplo de criação via CLI:

```bash
gh pr create \
  --title "feat: adiciona página de login" \
  --body "Implementa tela de login com validação de formulário." \
  --base main
```

### Code Review

- Comente linha por linha quando necessário
- Sugira melhorias de forma construtiva
- Aprove somente após entender e validar as mudanças
- **Nunca aprove seu próprio PR**

---

## Resumo rápido

1. Crie uma branch a partir de `main`
2. Faça commits semânticos durante o desenvolvimento
3. Abra um PR com título claro, descrição e prints (se visual)
4. Aguarde revisão — nunca aprove o próprio PR
5. Após aprovação, o merge é feito na `main`
