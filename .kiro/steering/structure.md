---
inclusion: always
---

# Estrutura e Contribuição — LogPulse IA

## Estrutura de Pastas

```
logpulse-ia/
├── src/                  # Código-fonte principal
│   ├── sources/          # Adaptadores de fonte de log (LogSource)
│   ├── parsers/          # Parsers por formato (JSON, plaintext, syslog)
│   ├── analyzer/         # Motor de detecção de anomalias
│   ├── ai/               # AI Engine (integração com LLMs)
│   └── cli/              # Interface de linha de comando
├── tests/                # Testes automatizados
├── logs/                 # Arquivos de log para testes e exemplos
├── docs/                 # Documentação adicional
└── README.md
```

- Todo código novo vai em `src/` no módulo correspondente
- Testes ficam em `tests/`, espelhando a estrutura de `src/`
- Arquivos `.log` de exemplo e fixtures ficam em `logs/`
- Documentação técnica adicional fica em `docs/`

---

## Proteção da Branch `main`

- **Nunca** faça commits diretamente na branch `main`
- Todo desenvolvimento ocorre em branches separadas, criadas a partir de `main`
- Alterações chegam à `main` exclusivamente via Pull Request, após revisão e aprovação

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

| Tipo       | Quando usar                       |
|------------|-----------------------------------|
| `feat`     | Nova funcionalidade               |
| `fix`      | Correção de bug                   |
| `docs`     | Documentação                      |
| `refactor` | Melhoria sem mudar função         |
| `style`    | Formatação, sem mudança de lógica |
| `test`     | Adição ou correção de testes      |
| `chore`    | Manutenção (build, deps, configs) |
| `perf`     | Melhoria de performance           |
| `ci`       | Mudanças em pipelines de CI/CD    |

### Exemplos reais

```bash
git commit -m "feat: adicionar login oauth"
git commit -m "fix: corrigir timeout"
git commit -m "docs: atualiza README com instruções de instalação"
git commit -m "refactor: simplifica parser de logs JSON"
```

---

## Pull Requests e Code Review

> ⚠️ Nunca aprove sua própria PR em projetos de equipe.

### Boas práticas no PR

- **Título claro** seguindo o padrão semântico
- **Descrição** explicando o que muda e o motivo
- **Prints** quando a alteração for visual

```bash
gh pr create \
  --title "feat: adiciona suporte a logs .gz" \
  --body "Implementa descompressão em memória para arquivos gzip." \
  --base main
```

### Code Review

- Comente linha por linha quando necessário
- Sugira melhorias de forma construtiva
- Aprove somente após entender e validar as mudanças
- **Nunca aprove seu próprio PR**

---

## Fluxo Resumido

1. Crie uma branch a partir de `main`
2. Faça commits semânticos durante o desenvolvimento
3. Abra um PR com título claro e descrição
4. Aguarde revisão — nunca aprove o próprio PR
5. Após aprovação, o merge é feito na `main`
