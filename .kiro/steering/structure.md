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
- Alterações chegam à `main` exclusivamente via Pull Request, com mínimo de **1 aprovação** de outro colaborador
- **Nunca aprove seu próprio PR**

### Nomenclatura de branches (validado automaticamente pelo CI)

Apenas dois prefixos são aceitos:

| Padrão           | Quando usar           |
|------------------|-----------------------|
| `feature/<nome>` | Nova funcionalidade   |
| `bugfix/<nome>`  | Correção de bug       |

Regras do `<nome>`:
- Apenas letras **minúsculas**, números e hífens
- Mínimo de **3 caracteres**
- Sem espaços, underscores ou maiúsculas

```
✅ feature/endpoint-logs-file
✅ feature/parser-drain3
✅ bugfix/correcao-timeout
✅ bugfix/fix-sqlite-connection

❌ minha-feature        (sem prefixo)
❌ feature/ab           (nome muito curto)
❌ feature/MinhaFeature (letra maiúscula)
❌ hotfix/bug-critico   (prefixo não permitido)
❌ chore/deps           (prefixo não permitido)
```

---

## Commits Semânticos (validado automaticamente pelo CI)

Todos os commits devem seguir o padrão:

```
<tipo>: <descrição curta no imperativo>
<tipo>(escopo): <descrição curta no imperativo>
```

### Tipos permitidos

| Tipo       | Quando usar                   |
|------------|-------------------------------|
| `feat`     | Nova funcionalidade           |
| `fix`      | Correção de bug               |
| `docs`     | Documentação                  |
| `refactor` | Melhoria sem mudar função     |

> ⚠️ Apenas estes 4 tipos são aceitos pelo CI. Commits com outros tipos (`chore`, `test`, `style`, `ci`, `perf`) serão **rejeitados**.

### Exemplos válidos

```bash
git commit -m "feat: adiciona endpoint POST api/v1/logs/file"
git commit -m "fix: corrige parsing de stacktrace Java"
git commit -m "docs: atualiza README com instruções de instalação"
git commit -m "refactor: simplifica lógica do serviço de diagnóstico"
git commit -m "feat(api): adiciona paginação no endpoint GET logs"
```

### Exemplos inválidos ❌

```
chore: atualiza dependências   ← tipo não permitido
test: adiciona testes          ← tipo não permitido
WIP                            ← sem tipo
ajustes                        ← sem tipo
```

---

## Pull Requests e Code Review

> ⚠️ Nunca aprove sua própria PR em projetos de equipe.

### Fluxo permitido pelo CI

```
feature/* → main   ✅
bugfix/*  → main   ✅
qualquer outra branch → main   ❌
```

### Boas práticas no PR

- **Título claro** seguindo o padrão semântico
- **Descrição** explicando o que muda e o motivo
- **Prints** quando a alteração for visual
- Mínimo de **1 aprovação** de outro colaborador antes do merge

```bash
gh pr create \
  --title "feat: adiciona endpoint de upload de arquivo de log" \
  --body "Implementa POST api/v1/logs/file com validação via Pydantic." \
  --base main
```

---

## Fluxo Resumido

1. Crie uma branch `feature/<nome>` ou `bugfix/<nome>` a partir de `main`
2. Faça commits usando apenas: `feat`, `fix`, `docs` ou `refactor`
3. Abra um PR com título claro e descrição
4. Aguarde **1 aprovação** de outro colaborador — nunca aprove o próprio PR
5. Após aprovação, o merge é feito na `main`
