# Documento de Requisitos — LogPulse IA

## Introdução

O **LogPulse IA** é uma ferramenta de linha de comando e biblioteca Python para ingestão, análise e investigação inteligente de logs. O sistema permite que engenheiros e times de operações carreguem logs de múltiplas fontes e formatos, detectem anomalias automaticamente e investiguem incidentes com suporte de IA, reduzindo o MTTR (Mean Time To Resolution) em ambientes de produção.

### Justificativa da Escolha de Linguagem

**Python** é a linguagem recomendada para este projeto pelos seguintes motivos:

- **Ecossistema de IA/ML maduro**: bibliotecas como `langchain`, `openai`, `transformers` e `sentence-transformers` são nativas do ecossistema Python, eliminando a necessidade de bridges ou wrappers.
- **Processamento de texto e logs**: bibliotecas como `re`, `pyparsing`, `loguru` e `structlog` oferecem suporte robusto para parsing de formatos variados.
- **Leitura de múltiplas fontes**: `boto3` (AWS CloudWatch), `google-cloud-logging`, `paramiko` (SSH/remoto), `watchdog` (arquivos locais em tempo real) são todas bibliotecas Python de primeira classe.
- **Prototipagem rápida**: a natureza interpretada do Python acelera iterações no desenvolvimento de regras de detecção e prompts de IA.
- **Comunidade e manutenção**: Python domina ferramentas de observabilidade e DevOps (Ansible, Airflow, Grafana plugins).

### Estratégia de Leitura de Logs

O sistema adotará uma arquitetura de **adaptadores de fonte** (Source Adapters), onde cada fonte de log implementa uma interface comum `LogSource`. Isso permite adicionar novas fontes sem alterar o núcleo do sistema.

Fontes suportadas na versão inicial:
- **Arquivo local** (`.log`, `.txt`, `.gz` comprimido): leitura sequencial com `open()` e `gzip`, suporte a `tail -f` via `watchdog`.
- **Stdin / pipe**: leitura de `sys.stdin` para integração com pipelines Unix (`cat app.log | logpulse analyze`).
- **JSON estruturado**: parsing via `json` stdlib ou `orjson` para alta performance.
- **Formato livre (plaintext)**: parsing via expressões regulares configuráveis pelo usuário.
- **Syslog**: parsing do formato RFC 3164/5424.

Fontes planejadas para versões futuras (fora do escopo deste spec):
- AWS CloudWatch Logs
- Google Cloud Logging
- Kubernetes pod logs via `kubectl`
- Elasticsearch / OpenSearch

---

## Glossário

- **LogPulse_IA**: o sistema como um todo, incluindo CLI, biblioteca e motor de análise.
- **Log_Source**: adaptador responsável por ler logs de uma origem específica (arquivo, stdin, etc.).
- **Log_Entry**: unidade atômica de log, contendo timestamp, nível de severidade, mensagem e metadados opcionais.
- **Log_Stream**: sequência ordenada de `Log_Entry` produzida por um `Log_Source`.
- **Parser**: componente que transforma texto bruto em `Log_Entry` estruturado.
- **Pretty_Printer**: componente que serializa um `Log_Entry` estruturado de volta para texto legível.
- **Analyzer**: componente que processa um `Log_Stream` e produz `Analysis_Result`.
- **Analysis_Result**: estrutura contendo anomalias detectadas, padrões identificados e sugestões de investigação.
- **AI_Engine**: componente que utiliza um modelo de linguagem (LLM) para enriquecer o `Analysis_Result` com diagnósticos e hipóteses.
- **CLI**: interface de linha de comando do LogPulse IA.
- **Severity_Level**: enumeração dos níveis de severidade: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- **MTTR**: Mean Time To Resolution — tempo médio de resolução de incidentes.

---

## Requisitos

### Requisito 1: Leitura de Logs de Arquivo Local

**User Story:** Como engenheiro de operações, quero carregar logs de arquivos locais em diferentes formatos, para que eu possa analisar incidentes sem precisar mover os arquivos para outro sistema.

#### Critérios de Aceitação

1. WHEN o usuário fornece um caminho de arquivo válido, THE Log_Source SHALL ler o arquivo e produzir um Log_Stream com todas as entradas contidas no arquivo.
2. WHEN o usuário fornece um arquivo com extensão `.gz`, THE Log_Source SHALL descomprimir o arquivo em memória e produzir o Log_Stream sem criar arquivos temporários em disco.
3. IF o caminho de arquivo fornecido não existir, THEN THE Log_Source SHALL retornar um erro descritivo indicando o caminho inválido e encerrar a leitura.
4. IF o arquivo existir mas o processo não tiver permissão de leitura, THEN THE Log_Source SHALL retornar um erro descritivo indicando a falta de permissão e encerrar a leitura.
5. WHEN o usuário ativa o modo de monitoramento contínuo (`--follow`), THE Log_Source SHALL monitorar o arquivo e emitir novas Log_Entry à medida que linhas forem adicionadas ao arquivo.
6. THE Log_Source SHALL suportar arquivos de até 10 GB sem carregar o conteúdo completo em memória, utilizando leitura linha a linha.

---

### Requisito 2: Leitura de Logs via Stdin

**User Story:** Como desenvolvedor, quero passar logs via pipe para o LogPulse IA, para que eu possa integrá-lo em pipelines Unix existentes sem alterar meu fluxo de trabalho.

#### Critérios de Aceitação

1. WHEN o LogPulse_IA recebe dados via stdin, THE Log_Source SHALL ler o stdin linha a linha e produzir um Log_Stream.
2. WHEN o stdin é encerrado (EOF), THE Log_Source SHALL finalizar o Log_Stream e sinalizar o término ao Analyzer.
3. THE CLI SHALL aceitar o caractere `-` como valor do argumento de fonte para indicar explicitamente leitura via stdin (ex: `logpulse analyze -`).

---

### Requisito 3: Parsing de Logs JSON Estruturado

**User Story:** Como engenheiro de plataforma, quero que o sistema interprete logs em formato JSON, para que os metadados estruturados sejam preservados e utilizados na análise.

#### Critérios de Aceitação

1. WHEN uma linha do Log_Stream contiver um objeto JSON válido, THE Parser SHALL deserializar a linha em um Log_Entry preservando todos os campos presentes no JSON.
2. THE Parser SHALL mapear automaticamente os campos `timestamp`, `level`, `message`, `msg`, `severity` e `time` para os atributos correspondentes do Log_Entry, independentemente de capitalização.
3. IF uma linha contiver JSON inválido (malformado), THEN THE Parser SHALL registrar a linha como Log_Entry com nível WARNING e mensagem original preservada no campo `raw`, sem interromper o processamento do Log_Stream.
4. THE Pretty_Printer SHALL serializar um Log_Entry de volta para uma linha JSON válida contendo todos os campos originais.
5. FOR ALL Log_Entry válidos produzidos pelo Parser a partir de JSON, o Pretty_Printer SHALL produzir uma saída que, quando re-parseada pelo Parser, resulte em um Log_Entry equivalente ao original (propriedade de round-trip).

---

### Requisito 4: Parsing de Logs em Formato Livre (Plaintext)

**User Story:** Como administrador de sistemas, quero que o sistema interprete logs em formato de texto livre com padrões comuns, para que eu possa analisar logs legados sem precisar reformatá-los.

#### Critérios de Aceitação

1. THE Parser SHALL reconhecer e extrair timestamp, nível de severidade e mensagem de logs no formato `[TIMESTAMP] [LEVEL] MESSAGE` sem configuração adicional do usuário.
2. THE Parser SHALL reconhecer o formato de log do Apache/Nginx Combined Log Format e extrair IP, método HTTP, URI, status code e tamanho da resposta como campos do Log_Entry.
3. THE Parser SHALL reconhecer o formato Syslog (RFC 3164) e extrair facility, severity, hostname, processo e mensagem como campos do Log_Entry.
4. WHERE o usuário fornecer uma expressão regular customizada com grupos nomeados, THE Parser SHALL utilizar essa expressão para extrair campos do Log_Entry a partir das linhas do Log_Stream.
5. IF uma linha não corresponder a nenhum padrão conhecido e nenhuma expressão customizada for fornecida, THEN THE Parser SHALL criar um Log_Entry com nível INFO, o conteúdo integral da linha no campo `message` e o campo `parsed` definido como `false`.
6. THE Pretty_Printer SHALL formatar um Log_Entry em texto legível por humanos, exibindo timestamp, nível de severidade e mensagem em uma única linha.

---

### Requisito 5: Normalização e Validação de Log_Entry

**User Story:** Como desenvolvedor do sistema, quero que todas as entradas de log sejam normalizadas para uma estrutura comum, para que o Analyzer possa processar logs de qualquer fonte de forma uniforme.

#### Critérios de Aceitação

1. THE Parser SHALL garantir que todo Log_Entry produzido contenha os campos obrigatórios: `timestamp` (datetime com timezone), `level` (Severity_Level), `message` (string não vazia) e `source` (identificador da Log_Source).
2. WHEN o campo `timestamp` de uma entrada não puder ser determinado, THE Parser SHALL atribuir o timestamp do momento da leitura e definir o campo `timestamp_inferred` como `true`.
3. WHEN o campo `level` de uma entrada não puder ser determinado, THE Parser SHALL atribuir o nível INFO e definir o campo `level_inferred` como `true`.
4. THE Parser SHALL normalizar variações de nomes de nível de severidade (ex: `WARN` → `WARNING`, `ERR` → `ERROR`, `FATAL` → `CRITICAL`) para os valores canônicos do Severity_Level.
5. FOR ALL Log_Entry produzidos pelo Parser, o campo `level` SHALL conter exclusivamente um dos valores: DEBUG, INFO, WARNING, ERROR ou CRITICAL.

---

### Requisito 6: Detecção de Anomalias e Padrões

**User Story:** Como engenheiro de operações, quero que o sistema detecte automaticamente anomalias e padrões suspeitos nos logs, para que eu possa identificar problemas sem precisar ler cada linha manualmente.

#### Critérios de Aceitação

1. WHEN o Analyzer processar um Log_Stream, THE Analyzer SHALL identificar e agrupar Log_Entry com mensagens semanticamente similares em clusters de padrão.
2. WHEN a frequência de Log_Entry com nível ERROR ou CRITICAL exceder 10 ocorrências em uma janela de 60 segundos, THE Analyzer SHALL sinalizar um spike de erros no Analysis_Result.
3. WHEN o Analyzer identificar uma sequência de Log_Entry que corresponda a um padrão de erro conhecido (ex: stack trace Java, Python traceback, panic do Go), THE Analyzer SHALL agrupar as linhas relacionadas em um único evento de erro no Analysis_Result.
4. THE Analyzer SHALL calcular e incluir no Analysis_Result a distribuição de Log_Entry por Severity_Level e por intervalo de tempo de 1 minuto.
5. IF o Log_Stream contiver menos de 2 Log_Entry, THEN THE Analyzer SHALL retornar um Analysis_Result indicando dados insuficientes para análise, sem executar detecção de anomalias.

---

### Requisito 7: Investigação com Suporte de IA

**User Story:** Como engenheiro de plantão, quero que o sistema utilize IA para sugerir hipóteses e próximos passos de investigação, para que eu possa resolver incidentes mais rapidamente mesmo sem conhecer profundamente o sistema afetado.

#### Critérios de Aceitação

1. WHEN o usuário solicitar análise com IA (`--ai`), THE AI_Engine SHALL receber o Analysis_Result e produzir um diagnóstico em linguagem natural descrevendo as anomalias identificadas.
2. WHEN o AI_Engine processar um Analysis_Result com pelo menos um spike de erros ou evento de erro agrupado, THE AI_Engine SHALL sugerir no mínimo 3 hipóteses de causa raiz ordenadas por probabilidade estimada.
3. WHEN o AI_Engine produzir hipóteses de causa raiz, THE AI_Engine SHALL incluir para cada hipótese pelo menos um comando ou ação de investigação sugerida.
4. IF a chave de API do LLM não estiver configurada e o usuário solicitar análise com IA, THEN THE AI_Engine SHALL retornar um erro descritivo indicando como configurar a chave de API, sem executar a análise.
5. WHERE o usuário configurar um modelo de LLM local (ex: Ollama), THE AI_Engine SHALL utilizar o endpoint local configurado em vez de APIs externas.
6. THE AI_Engine SHALL incluir no diagnóstico apenas informações derivadas do Log_Stream fornecido, sem inventar eventos ou timestamps não presentes nos logs originais.

---

### Requisito 8: Interface de Linha de Comando (CLI)

**User Story:** Como usuário do LogPulse IA, quero uma CLI intuitiva, para que eu possa executar análises rapidamente sem precisar escrever código Python.

#### Critérios de Aceitação

1. THE CLI SHALL expor o comando `logpulse analyze <fonte>` que aceita como `<fonte>` um caminho de arquivo, um diretório ou `-` para stdin.
2. THE CLI SHALL exibir o Analysis_Result em formato legível por humanos no stdout por padrão.
3. WHERE o usuário fornecer a flag `--output json`, THE CLI SHALL serializar o Analysis_Result completo como JSON válido no stdout.
4. WHERE o usuário fornecer a flag `--format <padrão>`, THE CLI SHALL utilizar o padrão fornecido para configurar o Parser de formato livre.
5. THE CLI SHALL retornar código de saída `0` quando a análise for concluída sem erros, `1` quando houver erros de entrada/configuração e `2` quando anomalias críticas forem detectadas no Log_Stream.
6. WHEN o usuário executar `logpulse --help` ou `logpulse analyze --help`, THE CLI SHALL exibir documentação de uso com descrição de todos os argumentos e flags disponíveis.

---

### Requisito 9: Configuração do Sistema

**User Story:** Como administrador, quero configurar o LogPulse IA via arquivo de configuração, para que eu possa padronizar o comportamento da ferramenta em diferentes ambientes sem repetir flags na linha de comando.

#### Critérios de Aceitação

1. THE LogPulse_IA SHALL carregar configurações a partir de um arquivo `logpulse.toml` localizado no diretório de trabalho atual ou em `~/.config/logpulse/logpulse.toml`.
2. WHEN ambos os arquivos de configuração existirem, THE LogPulse_IA SHALL mesclar as configurações, com o arquivo do diretório de trabalho tendo precedência sobre o arquivo global do usuário.
3. THE LogPulse_IA SHALL aceitar a variável de ambiente `LOGPULSE_API_KEY` como fonte da chave de API do LLM, com precedência sobre o valor definido no arquivo de configuração.
4. IF o arquivo de configuração existir mas contiver sintaxe TOML inválida, THEN THE LogPulse_IA SHALL retornar um erro descritivo indicando a linha do erro de sintaxe e encerrar sem executar a análise.
5. THE Pretty_Printer SHALL serializar uma configuração válida de volta para TOML válido.
6. FOR ALL configurações válidas lidas pelo LogPulse_IA, o Pretty_Printer SHALL produzir uma saída TOML que, quando re-lida pelo LogPulse_IA, resulte em uma configuração equivalente à original (propriedade de round-trip do parser de configuração).
