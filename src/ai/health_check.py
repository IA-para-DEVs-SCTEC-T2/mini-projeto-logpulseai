"""Verificação de disponibilidade do Ollama antes do processamento.

Implementa health check em duas camadas:
1. Conexão TCP na porta 11434 (rápido, verifica se o processo está rodando)
2. Requisição HTTP GET /api/tags (verifica se a API está respondendo)

Referência: RF-05.5 — Verificar se Ollama está disponível antes de processar.
"""

from __future__ import annotations

import logging
import socket

import httpx

from src.exceptions import AIEngineUnavailableError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_OLLAMA_HOST = "localhost"
_OLLAMA_PORT = 11434
_OLLAMA_BASE_URL = f"http://{_OLLAMA_HOST}:{_OLLAMA_PORT}"
_HEALTH_ENDPOINT = f"{_OLLAMA_BASE_URL}/api/tags"
_TCP_TIMEOUT_SECONDS = 3
_HTTP_TIMEOUT_SECONDS = 5


def check_ollama_tcp(
    host: str = _OLLAMA_HOST,
    port: int = _OLLAMA_PORT,
    timeout: float = _TCP_TIMEOUT_SECONDS,
) -> None:
    """Verifica conectividade TCP com o servidor Ollama.

    Tenta estabelecer uma conexão TCP com o host e porta especificados.
    Lança AIEngineUnavailableError se a conexão falhar.

    Args:
        host: Hostname do servidor Ollama.
        port: Porta do servidor Ollama.
        timeout: Timeout em segundos para a tentativa de conexão.

    Raises:
        AIEngineUnavailableError: Se não for possível conectar ao Ollama.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result != 0:
            raise AIEngineUnavailableError(
                f"Ollama não está disponível em {_OLLAMA_BASE_URL}. "
                "Verifique se o serviço está em execução: ollama serve"
            )
    except OSError as exc:
        raise AIEngineUnavailableError(
            f"Ollama não está disponível em {_OLLAMA_BASE_URL}. "
            "Verifique se o serviço está em execução: ollama serve"
        ) from exc


def check_ollama_http(
    base_url: str = _OLLAMA_BASE_URL,
    timeout: float = _HTTP_TIMEOUT_SECONDS,
) -> None:
    """Verifica se a API HTTP do Ollama está respondendo.

    Faz uma requisição GET ao endpoint /api/tags para confirmar
    que o servidor está operacional e aceitando requisições.

    Args:
        base_url: URL base do servidor Ollama.
        timeout: Timeout em segundos para a requisição HTTP.

    Raises:
        AIEngineUnavailableError: Se a API não responder com sucesso.
    """
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
        if response.status_code != 200:
            raise AIEngineUnavailableError(
                f"Ollama retornou status {response.status_code}. "
                "O serviço pode estar em estado inconsistente."
            )
    except httpx.ConnectError as exc:
        raise AIEngineUnavailableError(
            f"Não foi possível conectar à API do Ollama em {base_url}. "
            "Verifique se o serviço está em execução: ollama serve"
        ) from exc
    except httpx.TimeoutException as exc:
        raise AIEngineUnavailableError(
            f"Timeout ao verificar disponibilidade do Ollama em {base_url}. "
            "O serviço pode estar sobrecarregado."
        ) from exc


def check_ollama_available(
    host: str = _OLLAMA_HOST,
    port: int = _OLLAMA_PORT,
    base_url: str | None = None,
) -> None:
    """Verifica disponibilidade completa do Ollama (TCP + HTTP).

    Executa verificação em duas etapas:
    1. Conexão TCP (rápida, detecta se o processo está rodando)
    2. Requisição HTTP (confirma que a API está funcional)

    Args:
        host: Hostname do servidor Ollama.
        port: Porta do servidor Ollama.
        base_url: URL base para verificação HTTP (opcional).

    Raises:
        AIEngineUnavailableError: Se qualquer verificação falhar.
    """
    logger.debug("Verificando disponibilidade do Ollama em %s:%d", host, port)

    # Etapa 1: Verificação TCP
    check_ollama_tcp(host=host, port=port)

    # Etapa 2: Verificação HTTP
    url = base_url or f"http://{host}:{port}"
    check_ollama_http(base_url=url)

    logger.info("Ollama disponível e respondendo em %s:%d", host, port)
