"""Testes para verificação de disponibilidade do Ollama.

Cobre verificação TCP, HTTP e o fluxo completo de health check.
Referência: RF-05.5
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ai.health_check import (
    check_ollama_available,
    check_ollama_http,
    check_ollama_tcp,
)
from src.exceptions import AIEngineUnavailableError


# ---------------------------------------------------------------------------
# Testes de verificação TCP
# ---------------------------------------------------------------------------


class TestCheckOllamaTcp:
    """Testes para check_ollama_tcp."""

    @patch("src.ai.health_check.socket.socket")
    def test_tcp_connection_success(self, mock_socket_class: MagicMock) -> None:
        """Não lança exceção quando conexão TCP é bem-sucedida."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_sock

        # Não deve lançar exceção
        check_ollama_tcp(host="localhost", port=11434)

        mock_sock.settimeout.assert_called_once_with(3)
        mock_sock.connect_ex.assert_called_once_with(("localhost", 11434))
        mock_sock.close.assert_called_once()

    @patch("src.ai.health_check.socket.socket")
    def test_tcp_connection_refused(self, mock_socket_class: MagicMock) -> None:
        """Lança AIEngineUnavailableError quando conexão é recusada."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # Connection refused
        mock_socket_class.return_value = mock_sock

        with pytest.raises(AIEngineUnavailableError) as exc_info:
            check_ollama_tcp(host="localhost", port=11434)

        assert "ollama serve" in str(exc_info.value).lower()

    @patch("src.ai.health_check.socket.socket")
    def test_tcp_os_error_raises_unavailable(self, mock_socket_class: MagicMock) -> None:
        """Lança AIEngineUnavailableError quando ocorre OSError."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.side_effect = OSError("Network unreachable")
        mock_socket_class.return_value = mock_sock

        with pytest.raises(AIEngineUnavailableError):
            check_ollama_tcp(host="localhost", port=11434)

    @patch("src.ai.health_check.socket.socket")
    def test_tcp_custom_timeout(self, mock_socket_class: MagicMock) -> None:
        """Respeita timeout customizado."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_sock

        check_ollama_tcp(host="localhost", port=11434, timeout=10.0)

        mock_sock.settimeout.assert_called_once_with(10.0)


# ---------------------------------------------------------------------------
# Testes de verificação HTTP
# ---------------------------------------------------------------------------


class TestCheckOllamaHttp:
    """Testes para check_ollama_http."""

    @patch("src.ai.health_check.httpx.get")
    def test_http_success(self, mock_get: MagicMock) -> None:
        """Não lança exceção quando API retorna 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Não deve lançar exceção
        check_ollama_http(base_url="http://localhost:11434")

        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=5
        )

    @patch("src.ai.health_check.httpx.get")
    def test_http_non_200_raises_unavailable(self, mock_get: MagicMock) -> None:
        """Lança AIEngineUnavailableError quando API retorna status != 200."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        with pytest.raises(AIEngineUnavailableError) as exc_info:
            check_ollama_http(base_url="http://localhost:11434")

        assert "503" in str(exc_info.value)

    @patch("src.ai.health_check.httpx.get")
    def test_http_connect_error_raises_unavailable(self, mock_get: MagicMock) -> None:
        """Lança AIEngineUnavailableError quando não consegue conectar."""
        import httpx

        mock_get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(AIEngineUnavailableError) as exc_info:
            check_ollama_http(base_url="http://localhost:11434")

        assert "ollama serve" in str(exc_info.value).lower()

    @patch("src.ai.health_check.httpx.get")
    def test_http_timeout_raises_unavailable(self, mock_get: MagicMock) -> None:
        """Lança AIEngineUnavailableError quando ocorre timeout HTTP."""
        import httpx

        mock_get.side_effect = httpx.ReadTimeout("Read timed out")

        with pytest.raises(AIEngineUnavailableError) as exc_info:
            check_ollama_http(base_url="http://localhost:11434")

        assert "timeout" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Testes do fluxo completo
# ---------------------------------------------------------------------------


class TestCheckOllamaAvailable:
    """Testes para check_ollama_available (TCP + HTTP)."""

    @patch("src.ai.health_check.check_ollama_http")
    @patch("src.ai.health_check.check_ollama_tcp")
    def test_both_checks_pass(
        self, mock_tcp: MagicMock, mock_http: MagicMock
    ) -> None:
        """Não lança exceção quando TCP e HTTP passam."""
        mock_tcp.return_value = None
        mock_http.return_value = None

        # Não deve lançar exceção
        check_ollama_available()

        mock_tcp.assert_called_once()
        mock_http.assert_called_once()

    @patch("src.ai.health_check.check_ollama_http")
    @patch("src.ai.health_check.check_ollama_tcp")
    def test_tcp_fails_skips_http(
        self, mock_tcp: MagicMock, mock_http: MagicMock
    ) -> None:
        """Se TCP falha, não tenta HTTP e propaga exceção."""
        mock_tcp.side_effect = AIEngineUnavailableError("TCP failed")

        with pytest.raises(AIEngineUnavailableError):
            check_ollama_available()

        mock_tcp.assert_called_once()
        mock_http.assert_not_called()

    @patch("src.ai.health_check.check_ollama_http")
    @patch("src.ai.health_check.check_ollama_tcp")
    def test_tcp_passes_http_fails(
        self, mock_tcp: MagicMock, mock_http: MagicMock
    ) -> None:
        """Se TCP passa mas HTTP falha, propaga exceção HTTP."""
        mock_tcp.return_value = None
        mock_http.side_effect = AIEngineUnavailableError("HTTP failed")

        with pytest.raises(AIEngineUnavailableError) as exc_info:
            check_ollama_available()

        assert "HTTP failed" in str(exc_info.value)

    @patch("src.ai.health_check.check_ollama_http")
    @patch("src.ai.health_check.check_ollama_tcp")
    def test_custom_host_and_port(
        self, mock_tcp: MagicMock, mock_http: MagicMock
    ) -> None:
        """Aceita host e porta customizados."""
        mock_tcp.return_value = None
        mock_http.return_value = None

        check_ollama_available(host="192.168.1.100", port=8080)

        mock_tcp.assert_called_once_with(host="192.168.1.100", port=8080)
        mock_http.assert_called_once_with(base_url="http://192.168.1.100:8080")
