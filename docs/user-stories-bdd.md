# User Stories com BDD — LogPulse IA

---

## US-01: Upload de arquivo de log

**Como** desenvolvedor investigando um incidente,  
**Quero** enviar um arquivo .log ou .txt via API,  
**Para que** eu receba um diagnóstico automático do problema.

### Cenários BDD

```gherkin
Funcionalidade: Upload de arquivo de log

  Cenário: Upload bem-sucedido de arquivo .log
    Dado que o Ollama está disponível na porta 11434
    E eu tenho um arquivo "app.log" com conteúdo válido
    Quando eu envio POST /api/v1/logs/file com o arquivo
    Então a resposta deve ter status 201
    E o corpo deve conter "id", "analysis" e "diagnosis"
    E "diagnosis.hypotheses" deve ter pelo menos 3 itens

  Cenário: Rejeição de extensão inválida
    Dado que eu tenho um arquivo "dados.csv"
    Quando eu envio POST /api/v1/logs/file com o arquivo
    Então a resposta deve ter status 400
    E o corpo deve conter "Apenas arquivos .log e .txt são aceitos"

  Cenário: Rejeição de arquivo vazio
    Dado que eu tenho um arquivo "vazio.log" sem conteúdo
    Quando eu envio POST /api/v1/logs/file com o arquivo
    Então a resposta deve ter status 422
    E o corpo deve conter "vazio"

  Cenário: Ollama indisponível
    Dado que o Ollama NÃO está disponível
    E eu tenho um arquivo "app.log" com conteúdo válido
    Quando eu envio POST /api/v1/logs/file com o arquivo
    Então a resposta deve ter status 503
    E o corpo deve conter "indisponível"
```

---

## US-02: Envio de log via texto

**Como** desenvolvedor,  
**Quero** colar um trecho de log diretamente na API,  
**Para que** eu receba diagnóstico sem precisar criar um arquivo.

### Cenários BDD

```gherkin
Funcionalidade: Envio de log via texto

  Cenário: Envio bem-sucedido de texto
    Dado que o Ollama está disponível
    Quando eu envio POST /api/v1/logs/text com body:
      """
      {"content": "2024-01-15 10:00:00 ERROR Connection timeout\n2024-01-15 10:00:01 ERROR Retry failed"}
      """
    Então a resposta deve ter status 201
    E "analysis.error_count" deve ser >= 2

  Cenário: Texto vazio rejeitado
    Quando eu envio POST /api/v1/logs/text com body:
      """
      {"content": ""}
      """
    Então a resposta deve ter status 422

  Cenário: Texto excede limite de 100k caracteres
    Dado que eu tenho um texto com 100.001 caracteres
    Quando eu envio POST /api/v1/logs/text com esse conteúdo
    Então a resposta deve ter status 422
```

---

## US-03: Listagem paginada de logs

**Como** desenvolvedor,  
**Quero** listar os logs já analisados com paginação,  
**Para que** eu possa consultar diagnósticos anteriores.

### Cenários BDD

```gherkin
Funcionalidade: Listagem paginada

  Cenário: Listagem com dados existentes
    Dado que existem 25 logs no banco de dados
    Quando eu envio GET /api/v1/logs?page=1&page_size=10
    Então a resposta deve ter status 200
    E "items" deve ter 10 elementos
    E "total" deve ser 25
    E "pages" deve ser 3

  Cenário: Página vazia
    Dado que existem 5 logs no banco de dados
    Quando eu envio GET /api/v1/logs?page=2&page_size=10
    Então a resposta deve ter status 200
    E "items" deve ser uma lista vazia

  Cenário: Parâmetros inválidos
    Quando eu envio GET /api/v1/logs?page=0
    Então a resposta deve ter status 422
```

---

## US-04: Consulta de log por ID

**Como** desenvolvedor,  
**Quero** consultar um diagnóstico específico pelo ID,  
**Para que** eu possa revisitar uma análise anterior.

### Cenários BDD

```gherkin
Funcionalidade: Consulta por ID

  Cenário: Log encontrado
    Dado que existe um log com id "abc-123"
    Quando eu envio GET /api/v1/logs/abc-123
    Então a resposta deve ter status 200
    E o corpo deve conter "analysis" e "diagnosis"

  Cenário: Log não encontrado
    Quando eu envio GET /api/v1/logs/id-inexistente
    Então a resposta deve ter status 404
    E o corpo deve conter "não encontrado"
```

---

## US-05: Remoção de log

**Como** desenvolvedor,  
**Quero** remover um log do sistema,  
**Para que** eu possa limpar dados antigos ou irrelevantes.

### Cenários BDD

```gherkin
Funcionalidade: Remoção de log

  Cenário: Remoção bem-sucedida
    Dado que existe um log com id "abc-123"
    Quando eu envio DELETE /api/v1/logs/abc-123
    Então a resposta deve ter status 204
    E GET /api/v1/logs/abc-123 deve retornar 404

  Cenário: Remoção de log inexistente
    Quando eu envio DELETE /api/v1/logs/id-inexistente
    Então a resposta deve ter status 404
```

---

## US-06: Health check

**Como** operador do sistema,  
**Quero** verificar a saúde dos componentes,  
**Para que** eu saiba se a API, banco e Ollama estão funcionando.

### Cenários BDD

```gherkin
Funcionalidade: Health check

  Cenário: Todos os componentes saudáveis
    Dado que o banco de dados está acessível
    E o Ollama está disponível
    Quando eu envio GET /health
    Então a resposta deve ter status 200
    E "status" deve ser "healthy"

  Cenário: Ollama indisponível (degraded)
    Dado que o banco de dados está acessível
    E o Ollama NÃO está disponível
    Quando eu envio GET /health
    Então a resposta deve ter status 200
    E "status" deve ser "degraded"
    E "components.ollama.status" deve ser "unhealthy"
```

---

## US-07: Diagnóstico com hipóteses acionáveis

**Como** desenvolvedor,  
**Quero** que o diagnóstico contenha pelo menos 3 hipóteses com ações concretas,  
**Para que** eu saiba exatamente o que investigar.

### Cenários BDD

```gherkin
Funcionalidade: Qualidade do diagnóstico

  Cenário: Diagnóstico com hipóteses válidas
    Dado que eu enviei um log com erros de timeout
    Quando o diagnóstico é gerado
    Então "diagnosis.hypotheses" deve ter >= 3 itens
    E cada hipótese deve ter "description" não vazio
    E cada hipótese deve ter "probability" em ["alta", "média", "baixa"]
    E cada hipótese deve ter "action" não vazio
    E "diagnosis.summary" deve ser não vazio
    E "diagnosis.probable_cause" deve ser não vazio
```
