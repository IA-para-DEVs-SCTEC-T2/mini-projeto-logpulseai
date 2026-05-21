# Sessão de Teste — LogPulse IA

---

## 🧠 O que é esse projeto? (Para quem está começando)

Imagine que você tem um programa rodando no computador — pode ser um site, um bot, um sistema qualquer.
Enquanto esse programa funciona, ele vai **escrevendo mensagens** num arquivo de texto chamado **log**.
Essas mensagens dizem coisas como:

```
2026-05-18 10:00:01 [INFO] Servidor iniciado com sucesso
2026-05-18 10:00:45 [WARNING] Tentativa de conexão falhou, tentando novamente...
2026-05-18 10:01:02 [ERROR] Banco de dados não respondeu após 30 segundos
```

Quando algo dá errado, o desenvolvedor precisa **ler esses logs** para entender o que aconteceu.
O problema é que esses arquivos podem ter **centenas ou milhares de linhas** — é muito difícil ler tudo manualmente.

---

### 💡 O que o LogPulse IA faz?

O **LogPulse IA** é uma **API** (um programa que recebe pedidos e devolve respostas) que faz o seguinte:

1. **Você envia o log** — pode ser um arquivo `.log` ou `.txt`, ou colar o texto direto
2. **O sistema lê e analisa** — conta quantos erros tem, detecta padrões, agrupa problemas similares
3. **A IA (LLaMA 3 rodando no seu computador) pensa** — e sugere o que pode estar errado e como resolver
4. **Você recebe uma resposta organizada** — com os problemas encontrados e sugestões de ação

É como ter um **assistente especialista** que lê o log por você e te diz: *"olha, parece que o banco de dados está sobrecarregado, tenta fazer isso..."*

---

### 📬 Como funciona na prática?

Você faz um **pedido HTTP** para a API — pense nisso como apertar um botão num site, mas via código ou terminal.

**Você envia:**
```
POST http://localhost:8000/api/v1/logs/text
{ "content": "...seu log aqui..." }
```

**A API devolve um JSON** com a análise completa. JSON é um formato de texto organizado em chaves e valores, como uma lista estruturada.

---

### 📦 O que vem na resposta?

A resposta tem 5 partes principais:

#### 1. `id` — Identificador único
```json
"id": "d2c47bbf-b893-4ffb-924d-dcd5cbb1875e"
```
É como um número de protocolo. Você pode usar esse ID depois para consultar a análise novamente.

#### 2. `analyzed_at` — Quando foi analisado
```json
"analyzed_at": "2026-05-21T04:26:12Z"
```
Data e hora em que o sistema processou o seu log.

#### 3. `metrics` — Contadores do log
```json
"metrics": {
    "total_logs": 91,
    "errors": 3,
    "criticals": 0
}
```
- `total_logs` → quantas linhas o sistema leu
- `errors` → quantas linhas tinham a palavra ERROR
- `criticals` → quantas linhas tinham a palavra CRITICAL (mais grave que ERROR)

#### 4. `issues` — Problemas encontrados
```json
"issues": [
    {
        "title": "Groq API rate limit exceeded",
        "severity": "medium",
        "occurrences": 4,
        "first_seen": "2026-05-18T23:33:33Z",
        "last_seen": "2026-05-18T23:33:58Z",
        "recommendation": "Implementar retry com backoff exponencial",
        "affected_class": "GroqClient"
    }
]
```
Cada `issue` é um tipo de problema que apareceu no log:
- `title` → nome do problema
- `severity` → gravidade: `high` (grave), `medium` (médio), `low` (leve)
- `occurrences` → quantas vezes esse problema apareceu
- `first_seen` / `last_seen` → quando começou e quando foi a última vez
- `recommendation` → o que a IA sugere para resolver
- `affected_class` → em qual parte do código aconteceu

#### 5. `confidence` — Confiança da IA
```json
"confidence": 0.75
```
Um número de 0 a 1 que diz o quanto a IA tem certeza do diagnóstico:
- **0.0 a 0.4** → baixa confiança (poucos dados ou log muito simples)
- **0.4 a 0.7** → confiança moderada (encontrou padrões mas com dúvidas)
- **0.7 a 1.0** → alta confiança (padrão claro, diagnóstico confiável)

---

### 🚦 O que significam os códigos de resposta HTTP?

Quando você faz um pedido para a API, ela responde com um **código numérico** que indica se deu certo ou não:

| Código | Significado | Quando acontece |
|--------|-------------|-----------------|
| **201** | ✅ Criado com sucesso | Log analisado e salvo |
| **200** | ✅ OK | Consulta ou listagem bem-sucedida |
| **204** | ✅ Sem conteúdo | Log deletado com sucesso |
| **400** | ❌ Pedido inválido | Arquivo vazio ou extensão errada |
| **404** | ❌ Não encontrado | ID não existe no banco |
| **413** | ❌ Arquivo muito grande | Passou de 50MB |
| **415** | ❌ Formato não suportado | Enviou .pdf, .csv, etc. |
| **422** | ❌ Dados inválidos | Campo obrigatório faltando |
| **503** | ❌ Serviço indisponível | Ollama não está rodando |
| **504** | ❌ Timeout | Ollama demorou mais de 120 segundos |

---

### 🔄 Resumo do fluxo completo

```
Você                    LogPulse IA              Ollama (IA local)
  │                          │                         │
  │── envia o log ──────────>│                         │
  │                          │── analisa o log ──────> │
  │                          │                         │── pensa...
  │                          │<── diagnóstico ─────────│
  │<── resposta JSON ────────│                         │
  │                          │── salva no banco ──>    │
```

---

*Documento pessoal para registrar testes manuais da API.
Armazenado apenas localmente (listado no .gitignore).*

---

## 📁 Logs Fictícios Disponíveis para Teste

Três arquivos de log prontos em `logs/fixtures/`:

| Arquivo | Cenário | O que tem |
|---------|---------|-----------|
| `api-lenta.log` | API com banco de dados sobrecarregado | Timeouts SQL, Redis sem memória, Java stacktrace |
| `autenticacao-falha.log` | Ataque de brute force no login | Tentativas repetidas, IPs bloqueados, tokens inválidos |
| `ecommerce-crash.log` | E-commerce com gateway de pagamento fora | Pedidos falhando, pool esgotado, Python traceback, crash |

---

## Pré-requisitos

Antes de qualquer teste, verifique:

```powershell
# Terminal 1 — Ollama (deixe rodando)
ollama serve

# Terminal 2 — API (deixe rodando)
py -3.12 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Verificar saúde (deve retornar status "healthy")
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 5
```

---

## Teste 1 — API lenta com banco sobrecarregado

**Cenário:** Uma API de e-commerce começa a ter timeouts no banco de dados e o Redis fica sem memória.
**Esperado:** Issues de timeout SQL, CRITICAL do Redis, Java stacktrace detectado.

```powershell
# Envia o arquivo via terminal
curl -s -X POST "http://localhost:8000/api/v1/logs/file" `
     -F "file=@logs/fixtures/api-lenta.log;type=text/plain" `
     --max-time 180 | py -3.12 -m json.tool
```

**O que observar na resposta:**
- `metrics.errors` → deve ser alto (vários timeouts SQL)
- `metrics.criticals` → deve ter pelo menos 2 (Redis + banco)
- `issues` → deve listar o problema de timeout e Redis
- `confidence` → esperado acima de 0.6 (padrão claro)

---

## Teste 2 — Ataque de brute force no login

**Cenário:** Alguém tenta adivinhar a senha de contas repetidamente.
**Esperado:** Issues de segurança, IPs bloqueados, tentativas repetidas detectadas.

```powershell
curl -s -X POST "http://localhost:8000/api/v1/logs/file" `
     -F "file=@logs/fixtures/autenticacao-falha.log;type=text/plain" `
     --max-time 180 | py -3.12 -m json.tool
```

**O que observar na resposta:**
- `metrics.criticals` → deve ter 3 (2 IPs bloqueados + acesso não autorizado)
- `issues` → deve mencionar brute force ou tentativas repetidas
- `recommended_actions` → deve sugerir algo sobre bloqueio de IP ou rate limiting

---

## Teste 3 — E-commerce com crash total

**Cenário:** Gateway de pagamento cai, pool de conexões esgota, sistema encerra com erro.
**Esperado:** Muitos CRITICALs, Python traceback detectado, spike de erros.

```powershell
curl -s -X POST "http://localhost:8000/api/v1/logs/file" `
     -F "file=@logs/fixtures/ecommerce-crash.log;type=text/plain" `
     --max-time 180 | py -3.12 -m json.tool
```

**O que observar na resposta:**
- `metrics.criticals` → deve ser alto (vários CRITICALs)
- `issues` → deve listar falha no gateway e pool esgotado
- `confidence` → esperado alto (padrão muito claro de falha em cascata)

---

## Teste 4 — Log via TEXTO (colando direto)

**Cenário:** Você cola um trecho de log sem precisar de arquivo.

```powershell
$body = @{
    content = @"
2026-05-18 23:31:52 [WARNING] Tentativa 1/3 falhou: Page.goto: net::ERR_CONNECTION_CLOSED
2026-05-18 23:33:33 [WARNING] Groq falhou (429 Client Error: Too Many Requests). Usando correcao local.
2026-05-18 23:33:42 [WARNING] Groq falhou (429 Client Error: Too Many Requests). Usando correcao local.
2026-05-18 23:33:50 [WARNING] Groq falhou (429 Client Error: Too Many Requests). Usando correcao local.
2026-05-18 23:33:58 [WARNING] Groq falhou (429 Client Error: Too Many Requests). Usando correcao local.
2026-05-18 23:32:18 [INFO] Bot rodando... (CTRL+C para parar)
2026-05-18 23:32:38 [INFO] [Tarefa 1] CONCLUIDA com sucesso!
2026-05-18 23:33:01 [INFO] [Tarefa 2] CONCLUIDA com sucesso!
"@
} | ConvertTo-Json

$resposta = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/text" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -TimeoutSec 180

$resposta | ConvertTo-Json -Depth 10
```

---

## Teste 5 — Listar todas as análises salvas

**Após rodar os testes acima, consulte o histórico:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs?page=1&page_size=10" |
    ConvertTo-Json -Depth 5
```

---

## Teste 6 — Consultar análise específica por ID

```powershell
# Substitua pelo ID retornado em qualquer teste anterior
$id = "COLE-O-ID-AQUI"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/$id" |
    ConvertTo-Json -Depth 10
```

---

## Teste 7 — Deletar uma análise

```powershell
$id = "COLE-O-ID-AQUI"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/$id" -Method DELETE
# Esperado: sem corpo (HTTP 204 = deletado com sucesso)
```

---

## Teste 8 — Validações de erro (comportamento esperado)

```powershell
# Extensão inválida (.toml) → esperado HTTP 415
curl -s -X POST "http://localhost:8000/api/v1/logs/file" `
     -F "file=@pyproject.toml;type=text/plain" | py -3.12 -m json.tool

# Conteúdo vazio → esperado HTTP 422
$body = @{ content = "" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/logs/text" `
    -Method POST -Body $body -ContentType "application/json"

# ID inexistente → esperado HTTP 404
curl -s "http://localhost:8000/api/v1/logs/id-que-nao-existe" | py -3.12 -m json.tool
```

---

## Registro de Resultados

| Data | Teste | HTTP | ID Gerado | errors | criticals | confidence | Observações |
|------|-------|------|-----------|--------|-----------|------------|-------------|
| | Teste 1 — api-lenta.log | | | | | | |
| | Teste 2 — autenticacao-falha.log | | | | | | |
| | Teste 3 — ecommerce-crash.log | | | | | | |
| | Teste 4 — texto (bot log) | | | | | | |
| | Teste 5 — listagem | | | | | | |
| | Teste 6 — consulta por ID | | | | | | |
| | Teste 7 — delete | | | | | | |
| | Teste 8 — erros esperados | | | | | | |

---

## Links Úteis

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health
