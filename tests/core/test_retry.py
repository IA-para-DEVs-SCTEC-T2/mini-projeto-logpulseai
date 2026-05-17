"""Testes para módulo de retry com backoff exponencial.

Cobre cálculo de delay, retry com sucesso, falha após tentativas,
jitter e callback on_retry.

Referências: RF-05.7, RNF-08
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.retry import (
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_RETRIES,
    calculate_backoff_delay,
    retry_with_backoff,
)


# ---------------------------------------------------------------------------
# Testes de calculate_backoff_delay
# ---------------------------------------------------------------------------


class TestCalculateBackoffDelay:
    """Testes para cálculo de delay com backoff exponencial."""

    def test_primeira_tentativa_retorna_base_delay(self) -> None:
        """Primeira tentativa retorna aproximadamente o base_delay."""
        delay = calculate_backoff_delay(attempt=1, base_delay=1.0, jitter=0.0)
        assert delay == 1.0

    def test_segunda_tentativa_dobra_delay(self) -> None:
        """Segunda tentativa retorna 2x o base_delay."""
        delay = calculate_backoff_delay(attempt=2, base_delay=1.0, multiplier=2.0, jitter=0.0)
        assert delay == 2.0

    def test_terceira_tentativa_quadruplica_delay(self) -> None:
        """Terceira tentativa retorna 4x o base_delay."""
        delay = calculate_backoff_delay(attempt=3, base_delay=1.0, multiplier=2.0, jitter=0.0)
        assert delay == 4.0

    def test_delay_nao_excede_max_delay(self) -> None:
        """Delay nunca excede max_delay."""
        delay = calculate_backoff_delay(
            attempt=10, base_delay=1.0, multiplier=2.0, max_delay=30.0, jitter=0.0
        )
        assert delay == 30.0

    def test_jitter_adiciona_variacao(self) -> None:
        """Jitter adiciona variação ao delay."""
        delays = set()
        for _ in range(100):
            delay = calculate_backoff_delay(attempt=1, base_delay=1.0, jitter=0.1)
            delays.add(round(delay, 4))

        # Com jitter, deve haver variação nos delays
        assert len(delays) > 1

    def test_jitter_zero_retorna_delay_exato(self) -> None:
        """Sem jitter, delay é determinístico."""
        delay1 = calculate_backoff_delay(attempt=2, base_delay=1.0, jitter=0.0)
        delay2 = calculate_backoff_delay(attempt=2, base_delay=1.0, jitter=0.0)
        assert delay1 == delay2

    def test_multiplier_customizado(self) -> None:
        """Multiplier customizado é respeitado."""
        delay = calculate_backoff_delay(attempt=2, base_delay=1.0, multiplier=3.0, jitter=0.0)
        assert delay == 3.0

    def test_base_delay_customizado(self) -> None:
        """Base delay customizado é respeitado."""
        delay = calculate_backoff_delay(attempt=1, base_delay=5.0, jitter=0.0)
        assert delay == 5.0


# ---------------------------------------------------------------------------
# Testes de retry_with_backoff
# ---------------------------------------------------------------------------


class TestRetryWithBackoff:
    """Testes para retry_with_backoff."""

    @patch("src.core.retry.time.sleep")
    def test_sucesso_na_primeira_tentativa(self, mock_sleep: MagicMock) -> None:
        """Retorna resultado na primeira tentativa sem retry."""
        func = MagicMock(return_value="success")

        result = retry_with_backoff(func, max_retries=3)

        assert result == "success"
        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("src.core.retry.time.sleep")
    def test_sucesso_na_segunda_tentativa(self, mock_sleep: MagicMock) -> None:
        """Retorna resultado na segunda tentativa após falha na primeira."""
        func = MagicMock(side_effect=[ValueError("fail"), "success"])

        result = retry_with_backoff(
            func, max_retries=3, retryable_exceptions=(ValueError,)
        )

        assert result == "success"
        assert func.call_count == 2
        assert mock_sleep.call_count == 1

    @patch("src.core.retry.time.sleep")
    def test_falha_apos_todas_tentativas(self, mock_sleep: MagicMock) -> None:
        """Lança última exceção após esgotar todas as tentativas."""
        func = MagicMock(side_effect=TimeoutError("timeout"))

        with pytest.raises(TimeoutError) as exc_info:
            retry_with_backoff(
                func, max_retries=3, retryable_exceptions=(TimeoutError,)
            )

        assert "timeout" in str(exc_info.value)
        assert func.call_count == 3
        assert mock_sleep.call_count == 2  # sleep entre tentativas 1→2 e 2→3

    @patch("src.core.retry.time.sleep")
    def test_nao_retenta_excecao_nao_listada(self, mock_sleep: MagicMock) -> None:
        """Não retenta exceções que não estão em retryable_exceptions."""
        func = MagicMock(side_effect=KeyError("not retryable"))

        with pytest.raises(KeyError):
            retry_with_backoff(
                func, max_retries=3, retryable_exceptions=(ValueError,)
            )

        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("src.core.retry.time.sleep")
    def test_callback_on_retry_chamado(self, mock_sleep: MagicMock) -> None:
        """Callback on_retry é chamado antes de cada retry."""
        exc1 = ValueError("1")
        exc2 = ValueError("2")
        func = MagicMock(side_effect=[exc1, exc2, "ok"])
        on_retry = MagicMock()

        result = retry_with_backoff(
            func,
            max_retries=3,
            retryable_exceptions=(ValueError,),
            on_retry=on_retry,
        )

        assert result == "ok"
        assert on_retry.call_count == 2
        # Verifica argumentos do callback
        on_retry.assert_any_call(1, exc1)
        on_retry.assert_any_call(2, exc2)

    @patch("src.core.retry.time.sleep")
    def test_delays_crescem_exponencialmente(self, mock_sleep: MagicMock) -> None:
        """Delays entre tentativas crescem exponencialmente."""
        func = MagicMock(side_effect=ValueError("fail"))

        with pytest.raises(ValueError):
            retry_with_backoff(
                func,
                max_retries=4,
                retryable_exceptions=(ValueError,),
                base_delay=1.0,
                multiplier=2.0,
                jitter=0.0,
            )

        # 3 sleeps: entre tentativas 1→2, 2→3, 3→4
        assert mock_sleep.call_count == 3
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]

    @patch("src.core.retry.time.sleep")
    def test_max_retries_um_nao_faz_retry(self, mock_sleep: MagicMock) -> None:
        """Com max_retries=1, não há retry."""
        func = MagicMock(side_effect=ValueError("fail"))

        with pytest.raises(ValueError):
            retry_with_backoff(
                func, max_retries=1, retryable_exceptions=(ValueError,)
            )

        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("src.core.retry.time.sleep")
    def test_multiplas_excecoes_retryable(self, mock_sleep: MagicMock) -> None:
        """Retenta para múltiplos tipos de exceção."""
        func = MagicMock(
            side_effect=[TimeoutError("t"), ConnectionError("c"), "ok"]
        )

        result = retry_with_backoff(
            func,
            max_retries=3,
            retryable_exceptions=(TimeoutError, ConnectionError),
        )

        assert result == "ok"
        assert func.call_count == 3
