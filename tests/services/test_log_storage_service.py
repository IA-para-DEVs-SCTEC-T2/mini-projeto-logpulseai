"""Testes para LogStorageService — operações CRUD de logs.

Cobre get_by_id, list_logs com paginação e delete_log.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.exceptions import StorageError
from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
    LogListResponse,
    SeverityLevel,
)
from src.services.log_storage_service import LogStorageService


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------


def _make_response(log_id: str = "uuid-123") -> LogAnalysisResponse:
    """Cria um LogAnalysisResponse de teste."""
    return LogAnalysisResponse(
        id=log_id,
        analysis=AnalysisResult(total_entries=5, error_count=3, warning_count=1),
        diagnosis=AIDiagnosis(
            summary="Problema detectado.",
            probable_cause="Causa provável.",
            hypotheses=[
                Hypothesis(description="H1", probability="alta", action="Ação 1"),
                Hypothesis(description="H2", probability="média", action="Ação 2"),
                Hypothesis(description="H3", probability="baixa", action="Ação 3"),
            ],
            suggested_fix="Correção sugerida.",
            confidence=0.8,
        ),
        created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        total_entries=5,
        summary="Problema detectado.",
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Repository mock com operações assíncronas."""
    repo = AsyncMock()
    repo.get_by_id.return_value = _make_response()
    repo.list_paginated.return_value = [_make_response(f"uuid-{i}") for i in range(5)]
    repo.delete.return_value = True
    return repo


@pytest.fixture
def service(mock_repository: AsyncMock) -> LogStorageService:
    """Instância do serviço com repositório mockado."""
    return LogStorageService(repository=mock_repository)


# ---------------------------------------------------------------------------
# Testes de get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    """Testes para LogStorageService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_retorna_log_existente(
        self, service: LogStorageService, mock_repository: AsyncMock
    ) -> None:
        """Retorna LogAnalysisResponse quando log existe."""
        result = await service.get_by_id("uuid-123")

        assert result is not None
        assert result.id == "uuid-123"
        mock_repository.get_by_id.assert_called_once_with("uuid-123")

    @pytest.mark.asyncio
    async def test_retorna_none_quando_nao_existe(
        self, mock_repository: AsyncMock
    ) -> None:
        """Retorna None quando log não existe."""
        mock_repository.get_by_id.return_value = None
        service = LogStorageService(repository=mock_repository)

        result = await service.get_by_id("uuid-inexistente")

        assert result is None

    @pytest.mark.asyncio
    async def test_propaga_storage_error(self, mock_repository: AsyncMock) -> None:
        """Propaga StorageError do repositório."""
        mock_repository.get_by_id.side_effect = StorageError("DB read failed")
        service = LogStorageService(repository=mock_repository)

        with pytest.raises(StorageError):
            await service.get_by_id("uuid-123")

    @pytest.mark.asyncio
    async def test_wraps_excecao_generica_em_storage_error(
        self, mock_repository: AsyncMock
    ) -> None:
        """Encapsula exceção genérica em StorageError."""
        mock_repository.get_by_id.side_effect = RuntimeError("Unexpected")
        service = LogStorageService(repository=mock_repository)

        with pytest.raises(StorageError) as exc_info:
            await service.get_by_id("uuid-123")

        assert "Unexpected" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Testes de list_logs
# ---------------------------------------------------------------------------


class TestListLogs:
    """Testes para LogStorageService.list_logs()."""

    @pytest.mark.asyncio
    async def test_retorna_lista_paginada(
        self, service: LogStorageService
    ) -> None:
        """Retorna LogListResponse com itens e metadados de paginação."""
        result = await service.list_logs(page=1, page_size=20)

        assert isinstance(result, LogListResponse)
        assert len(result.items) == 5
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_calcula_total_de_paginas(
        self, mock_repository: AsyncMock
    ) -> None:
        """Calcula corretamente o total de páginas."""
        # 15 itens no total, page_size=5 → 3 páginas
        items_page = [_make_response(f"uuid-{i}") for i in range(5)]
        all_items = [_make_response(f"uuid-{i}") for i in range(15)]

        # list_paginated é chamado 2x: uma para a página, outra para o total
        mock_repository.list_paginated.side_effect = [items_page, all_items]
        service = LogStorageService(repository=mock_repository)

        result = await service.list_logs(page=1, page_size=5)

        assert result.total == 15
        assert result.pages == 3

    @pytest.mark.asyncio
    async def test_pagina_vazia_retorna_zero_paginas(
        self, mock_repository: AsyncMock
    ) -> None:
        """Retorna 0 páginas quando não há registros."""
        mock_repository.list_paginated.return_value = []
        service = LogStorageService(repository=mock_repository)

        result = await service.list_logs(page=1, page_size=20)

        assert result.total == 0
        assert result.pages == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_valida_page_minimo(self, service: LogStorageService) -> None:
        """Lança ValueError quando page < 1."""
        with pytest.raises(ValueError) as exc_info:
            await service.list_logs(page=0, page_size=20)

        assert "page" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_valida_page_size_minimo(self, service: LogStorageService) -> None:
        """Lança ValueError quando page_size < 1."""
        with pytest.raises(ValueError) as exc_info:
            await service.list_logs(page=1, page_size=0)

        assert "page_size" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_valida_page_size_maximo(self, service: LogStorageService) -> None:
        """Lança ValueError quando page_size > 100."""
        with pytest.raises(ValueError) as exc_info:
            await service.list_logs(page=1, page_size=101)

        assert "page_size" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_propaga_storage_error(self, mock_repository: AsyncMock) -> None:
        """Propaga StorageError do repositório."""
        mock_repository.list_paginated.side_effect = StorageError("DB error")
        service = LogStorageService(repository=mock_repository)

        with pytest.raises(StorageError):
            await service.list_logs(page=1, page_size=20)


# ---------------------------------------------------------------------------
# Testes de delete_log
# ---------------------------------------------------------------------------


class TestDeleteLog:
    """Testes para LogStorageService.delete_log()."""

    @pytest.mark.asyncio
    async def test_retorna_true_quando_removido(
        self, service: LogStorageService, mock_repository: AsyncMock
    ) -> None:
        """Retorna True quando log é removido com sucesso."""
        result = await service.delete_log("uuid-123")

        assert result is True
        mock_repository.delete.assert_called_once_with("uuid-123")

    @pytest.mark.asyncio
    async def test_retorna_false_quando_nao_existe(
        self, mock_repository: AsyncMock
    ) -> None:
        """Retorna False quando log não existe."""
        mock_repository.delete.return_value = False
        service = LogStorageService(repository=mock_repository)

        result = await service.delete_log("uuid-inexistente")

        assert result is False

    @pytest.mark.asyncio
    async def test_propaga_storage_error(self, mock_repository: AsyncMock) -> None:
        """Propaga StorageError do repositório."""
        mock_repository.delete.side_effect = StorageError("DB delete failed")
        service = LogStorageService(repository=mock_repository)

        with pytest.raises(StorageError):
            await service.delete_log("uuid-123")

    @pytest.mark.asyncio
    async def test_wraps_excecao_generica_em_storage_error(
        self, mock_repository: AsyncMock
    ) -> None:
        """Encapsula exceção genérica em StorageError."""
        mock_repository.delete.side_effect = RuntimeError("Unexpected")
        service = LogStorageService(repository=mock_repository)

        with pytest.raises(StorageError) as exc_info:
            await service.delete_log("uuid-123")

        assert "Unexpected" in str(exc_info.value)
