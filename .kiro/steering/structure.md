---
inclusion: always
---

# Estrutura e Contribuição — LogPulse IA

## Estrutura de Pastas

```
logpulse-ia/
├── src/                  # Código-fonte principal
│   ├── api/              # Rotas e controllers FastAPI
│   │   └── v1/
│   │       └── logs/     # Endpoints de logs (file, text, CRUD)
│   ├── services/         # Lógica de negócio (análise, diagnóstico)
│   ├── parsers/          # Integração com Drain3 para parsing de logs
│   ├── ai/               # Integração com Ollama/LLaMA 3 via OpenAI SDK
│   ├── models/           # Modelos SQLite e schemas Pydantic
│   └── core/             # Configurações, dependências e utilitários
├── tests/                # Testes automatizados (cobertura mínima 30%)
├── logs/                 # Arquivos de log para testes e exemplos
├── docs/                 # Documentação adicional
└── README.md
```

- Todo código novo vai em `src/` no módulo correspondente
- Testes ficam em `tests/`, espelhando a estrutura de `src/`
- Arquivos `.log` e `.txt` de exemplo e fixtures ficam em `logs/`
- Documentação técnica adicional fica em `docs/`

---

## Proteção da Branch `main`

- **Nunca** faça commits diretamente na branch `main`
- Todo desenvolvimento ocorre em branches separadas, criadas a partir de `main`
- Alterações chegam à `main` exclusivamente via Pull Request, após revisão e aprovação

### Nomenclatura de branches

Use o padrão: `<tipo>/<descricao-curta>`

Exemplos:
- `feat/endpoint-logs-file`
- `fix/correcao-parser-drain3`
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
git commit -m "feat: adiciona endpoint POST api/v1/logs/file"
git commit -m "fix: corrige parsing de stacktrace Java"
git commit -m "docs: atualiza README com instruções de instalação"
git commit -m "test: adiciona testes para o serviço de diagnóstico"
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
  --title "feat: adiciona endpoint de upload de arquivo de log" \
  --body "Implementa POST api/v1/logs/file com validação via Pydantic." \
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
