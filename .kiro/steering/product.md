---
inclusion: always
---

# Produto — LogPulse IA

## Visão Geral

**LogPulse IA** é uma ferramenta CLI e biblioteca Python para ingestão, análise e investigação inteligente de logs. O objetivo é reduzir o MTTR (Mean Time To Resolution) de incidentes em produção com suporte de IA.

## Funcionalidades

- Leitura de logs de arquivos locais (`.log`, `.txt`, `.gz`) e via stdin/pipe
- Parsing automático de JSON estruturado, Apache/Nginx, Syslog e formato livre
- Detecção automática de anomalias e spikes de erros
- Investigação com IA: hipóteses de causa raiz e sugestões de ação
- Suporte a LLMs locais via Ollama e APIs externas (OpenAI)
- CLI intuitiva: `logpulse analyze <fonte>`

## Comandos Principais

```bash
logpulse analyze <fonte>               # analisa logs de arquivo ou stdin (-)
logpulse analyze <fonte> --ai          # análise com suporte de IA
logpulse analyze <fonte> --follow      # monitoramento contínuo (tail -f)
logpulse analyze <fonte> --output json # saída em JSON
logpulse --help                        # documentação de uso
```

## Códigos de Saída da CLI

| Código | Significado                                 |
|--------|---------------------------------------------|
| `0`    | Análise concluída sem erros                 |
| `1`    | Erro de entrada ou configuração             |
| `2`    | Anomalias críticas detectadas no Log_Stream |

## Configuração

O sistema carrega configurações de `logpulse.toml` no diretório atual ou em `~/.config/logpulse/logpulse.toml`. A variável de ambiente `LOGPULSE_API_KEY` tem precedência sobre o arquivo de configuração.

```toml
[ai]
model = "gpt-4o"
# ou para LLM local:
# endpoint = "http://localhost:11434"

[parser]
format = "json"  # json | plaintext | syslog | auto
```
