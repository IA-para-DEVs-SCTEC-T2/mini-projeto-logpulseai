"""Módulo de resiliência — retry com backoff exponencial.

Fornece decorador e utilitário para retry com backoff exponencial,
jitter e configuração de timeout. Reutilizável por qualquer componente.

Referências: RF-05.7, RNF-08
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Constantes padrão
# ---------------------------------------------------------------------------

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # segundos
DEFAULT_MAX_DELAY = 30.0  # segundos
DEFAULT_MULTIPLIER = 2.0
DEFAULT_JITTER = 0.1  # 10% de jitter


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = DEFAULT_BASE_DELAY,
    multiplier: float = DEFAULT_MULTIPLIER,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter: float = DEFAULT_JITTER,
) -> float:
    """Calcula o delay para uma tentativa com backoff exponencial e jitter.

    Fórmula: min(base_delay * multiplier^(attempt-1) + jitter_random, max_delay)

    Args:
        attempt: Número da tentativa (1-indexed, delay é para ANTES desta tentativa).
        base_delay: Delay base em segundos.
        multiplier: Fator multiplicador para cada tentativa.
        max_delay: Delay máximo em segundos (cap).
        jitter: Fração de jitter aleatório (0.0 a 1.0).

    Returns:
        Delay em segundos para aguardar antes da próxima tentativa.

    Example:
        >>> calculate_backoff_delay(1)  # ~1.0s
        >>> calculate_backoff_delay(2)  # ~2.0s
        >>> calculate_backoff_delay(3)  # ~4.0s
    """
    delay = base_delay * (multiplier ** (attempt - 1))
    delay = min(delay, max_delay)

    # Adiciona jitter aleatório para evitar thundering herd
    if jitter > 0:
        jitter_amount = delay * jitter * random.random()
        delay += jitter_amount

    return delay


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = DEFAULT_MAX_RETRIES,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    base_delay: float = DEFAULT_BASE_DELAY,
    multiplier: float = DEFAULT_MULTIPLIER,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter: float = DEFAULT_JITTER,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Executa uma função com retry e backoff exponencial.

    Tenta executar `func` até `max_retries` vezes. Entre tentativas,
    aguarda com backoff exponencial. Apenas exceções listadas em
    `retryable_exceptions` acionam retry.

    Args:
        func: Função sem argumentos a ser executada.
        max_retries: Número máximo de tentativas.
        retryable_exceptions: Tupla de exceções que acionam retry.
        base_delay: Delay base em segundos.
        multiplier: Fator multiplicador.
        max_delay: Delay máximo em segundos.
        jitter: Fração de jitter (0.0 a 1.0).
        on_retry: Callback opcional chamado antes de cada retry.

    Returns:
        Resultado da execução bem-sucedida de `func`.

    Raises:
        A última exceção capturada se todas as tentativas falharem.

    Example:
        >>> result = retry_with_backoff(
        ...     lambda: api_call(),
        ...     max_retries=3,
        ...     retryable_exceptions=(TimeoutError, ConnectionError),
        ... )
    """
    last_exception: BaseException | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except retryable_exceptions as exc:
            last_exception = exc
            logger.warning(
                "Tentativa %d/%d falhou: %s: %s",
                attempt,
                max_retries,
                type(exc).__name__,
                str(exc)[:200],
            )

            if on_retry is not None:
                on_retry(attempt, exc)

            if attempt < max_retries:
                delay = calculate_backoff_delay(
                    attempt=attempt,
                    base_delay=base_delay,
                    multiplier=multiplier,
                    max_delay=max_delay,
                    jitter=jitter,
                )
                logger.info(
                    "Aguardando %.2fs antes da tentativa %d",
                    delay,
                    attempt + 1,
                )
                time.sleep(delay)

    # Se chegou aqui, todas as tentativas falharam
    assert last_exception is not None
    raise last_exception
