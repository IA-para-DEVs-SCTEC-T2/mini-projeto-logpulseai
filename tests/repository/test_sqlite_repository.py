"""Testes para SQLiteLogRepository e interface LogRepository.

Usa banco de dados SQLite real em diretório temporário (tmp_path fixture),
sem mocks, para validar o comportamento real de persistência.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio

from src.models.schemas import (
    AIDiagnosis,
    AnalysisResult,
    Hypothesis,
    LogAnalysisResponse,
    SeverityLevel,
)
from src.repository.base import LogRepository
from src.repository.sqlite_repository import SQLiteLogRepository

# ---------------------------------------------------------------------------
# Helpers para criação de dados de teste
# ---------------------------------------------------------------------------


def make_diagnosis() -> AIDiagnosis:
    """Cria um AIDiagnosis de exemplo para testes."""
    return AIDiagnosis(
        summary="Falha de conexao",
        probable_cause="Pool esgotado",
        hypotheses=[
            Hypothesis(description="H1", probability="alta", action="Acao 1"),
            Hypothesis(description="H2", probability="média", action="Acao 2"),
            Hypothesis(description="H3", probability="baixa", action="Acao 3"),
        ],
    )


def make_analysis() -> AnalysisResult:
    """Cria um AnalysisResult de exemplo para testes."""
    return AnalysisResult(
        total_entries=10,
        error_count=5,
        warning_count=3,
        severity_distribution={
            SeverityLevel.ERROR: 5,
            SeverityLevel.WARNING: 3,
            SeverityLevel.INFO: 2,
        },
    )


# ---------------------------------------------------------------------------
# Fixture principal
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def repo(tmp_path: Path) -> SQLiteLogRepository:
    """Cria e inicializa um SQLiteLogRepository em diretório temporário."""
    db_path = str(tmp_path / "test_logpulse.db")
    repository = SQLiteLogRepository(db_path=db_path)
    await repository.initialize()
    return repository


# ---------------------------------------------------------------------------
# Testes de interface e herança
# ---------------------------------------------------------------------------


def test_log_repository_cannot_be_instantiated_directly() -> None:
    """LogRepository é abstrata e não pode ser instanciada diretamente."""
    with pytest.raises(TypeError):
        LogRepository()  # type: ignore[abstract]


def test_sqlite_repository_is_subclass_of_log_repository() -> None:
    """SQLiteLogRepository deve ser subclasse de LogRepository."""
    assert issubclass(SQLiteLogRepository, LogRepository)


# ---------------------------------------------------------------------------
# Testes de create()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_returns_valid_uuid(repo: SQLiteLogRepository) -> None:
    """create() deve retornar uma string UUID válida."""
    log_id = await repo.create("conteudo do log", make_analysis(), make_diagnosis())

    # Valida que é um UUID válido (não lança exceção)
    parsed = uuid.UUID(log_id)
    assert str(parsed) == log_id


@pytest.mark.asyncio
async def test_create_persists_data(repo: SQLiteLogRepository) -> None:
    """create() deve persistir dados que podem ser recuperados posteriormente."""
    content = "linha de log de teste"
    log_id = await repo.create(content, make_analysis(), make_diagnosis())

    record = await repo.get_by_id(log_id)
    assert record is not None
    assert record.id == log_id


# ---------------------------------------------------------------------------
# Testes de get_by_id()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_nonexistent_id(repo: SQLiteLogRepository) -> None:
    """get_by_id() deve retornar None para um ID que não existe."""
    result = await repo.get_by_id(str(uuid.uuid4()))
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_returns_correct_response(repo: SQLiteLogRepository) -> None:
    """get_by_id() deve retornar LogAnalysisResponse correto para ID existente."""
    analysis = make_analysis()
    diagnosis = make_diagnosis()
    log_id = await repo.create("log content", analysis, diagnosis)

    record = await repo.get_by_id(log_id)

    assert record is not None
    assert isinstance(record, LogAnalysisResponse)
    assert record.id == log_id


# ---------------------------------------------------------------------------
# Testes de round-trip (create → get_by_id)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roundtrip_preserves_analysis_result(repo: SQLiteLogRepository) -> None:
    """Round-trip: create() + get_by_id() deve preservar dados de AnalysisResult."""
    analysis = make_analysis()
    diagnosis = make_diagnosis()
    log_id = await repo.create("log content", analysis, diagnosis)

    record = await repo.get_by_id(log_id)

    assert record is not None
    assert record.analysis.total_entries == analysis.total_entries
    assert record.analysis.error_count == analysis.error_count
    assert record.analysis.warning_count == analysis.warning_count
    assert record.analysis.severity_distribution == analysis.severity_distribution


@pytest.mark.asyncio
async def test_roundtrip_preserves_ai_diagnosis(repo: SQLiteLogRepository) -> None:
    """Round-trip: create() + get_by_id() deve preservar dados de AIDiagnosis."""
    analysis = make_analysis()
    diagnosis = make_diagnosis()
    log_id = await repo.create("log content", analysis, diagnosis)

    record = await repo.get_by_id(log_id)

    assert record is not None
    assert record.diagnosis.summary == diagnosis.summary
    assert record.diagnosis.probable_cause == diagnosis.probable_cause
    assert len(record.diagnosis.hypotheses) == len(diagnosis.hypotheses)
    assert record.diagnosis.hypotheses[0].description == diagnosis.hypotheses[0].description
    assert record.diagnosis.hypotheses[0].probability == diagnosis.hypotheses[0].probability
    assert record.diagnosis.hypotheses[0].action == diagnosis.hypotheses[0].action


# ---------------------------------------------------------------------------
# Testes de list_paginated()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_paginated_returns_empty_when_no_records(repo: SQLiteLogRepository) -> None:
    """list_paginated() deve retornar lista vazia quando não há registros."""
    result = await repo.list_paginated(page=1, page_size=10)
    assert result == []


@pytest.mark.asyncio
async def test_list_paginated_returns_correct_page(repo: SQLiteLogRepository) -> None:
    """list_paginated() deve retornar a página correta de resultados."""
    # Cria 3 registros
    for i in range(3):
        await repo.create(f"log {i}", make_analysis(), make_diagnosis())

    result = await repo.list_paginated(page=1, page_size=10)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_paginated_respects_page_size(repo: SQLiteLogRepository) -> None:
    """list_paginated() deve respeitar o page_size informado."""
    # Cria 5 registros
    for i in range(5):
        await repo.create(f"log {i}", make_analysis(), make_diagnosis())

    result = await repo.list_paginated(page=1, page_size=3)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_paginated_page2_differs_from_page1(repo: SQLiteLogRepository) -> None:
    """list_paginated() página 2 deve retornar resultados diferentes da página 1."""
    # Cria 4 registros
    for i in range(4):
        await repo.create(f"log {i}", make_analysis(), make_diagnosis())

    page1 = await repo.list_paginated(page=1, page_size=2)
    page2 = await repo.list_paginated(page=2, page_size=2)

    assert len(page1) == 2
    assert len(page2) == 2

    ids_page1 = {r.id for r in page1}
    ids_page2 = {r.id for r in page2}
    assert ids_page1.isdisjoint(ids_page2), "Páginas não devem ter registros em comum"


# ---------------------------------------------------------------------------
# Testes de delete()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_returns_true_for_existing_id(repo: SQLiteLogRepository) -> None:
    """delete() deve retornar True ao remover um registro existente."""
    log_id = await repo.create("log content", make_analysis(), make_diagnosis())

    result = await repo.delete(log_id)
    assert result is True


@pytest.mark.asyncio
async def test_delete_returns_false_for_nonexistent_id(repo: SQLiteLogRepository) -> None:
    """delete() deve retornar False para um ID que não existe."""
    result = await repo.delete(str(uuid.uuid4()))
    assert result is False


@pytest.mark.asyncio
async def test_delete_actually_removes_record(repo: SQLiteLogRepository) -> None:
    """delete() deve remover o registro — get_by_id retorna None após deleção."""
    log_id = await repo.create("log content", make_analysis(), make_diagnosis())

    await repo.delete(log_id)

    record = await repo.get_by_id(log_id)
    assert record is None


# ---------------------------------------------------------------------------
# Testes de comportamento geral
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_creates_list_returns_all(repo: SQLiteLogRepository) -> None:
    """Múltiplos creates devem resultar em todos os registros na listagem."""
    ids = []
    for i in range(5):
        log_id = await repo.create(f"log {i}", make_analysis(), make_diagnosis())
        ids.append(log_id)

    result = await repo.list_paginated(page=1, page_size=10)
    result_ids = {r.id for r in result}

    assert len(result) == 5
    for log_id in ids:
        assert log_id in result_ids


@pytest.mark.asyncio
async def test_created_at_is_set_automatically(repo: SQLiteLogRepository) -> None:
    """created_at deve ser definido automaticamente ao criar um registro."""
    before = datetime.now(UTC)
    log_id = await repo.create("log content", make_analysis(), make_diagnosis())
    after = datetime.now(UTC)

    record = await repo.get_by_id(log_id)

    assert record is not None
    assert record.created_at is not None
    assert isinstance(record.created_at, datetime)
    # Verifica que o timestamp está dentro do intervalo esperado
    assert before <= record.created_at <= after


@pytest.mark.asyncio
async def test_list_ordered_by_created_at_desc(repo: SQLiteLogRepository) -> None:
    """list_paginated() deve retornar registros ordenados por created_at DESC."""
    import asyncio

    # Cria registros com pequeno intervalo para garantir ordem
    ids_in_order = []
    for i in range(3):
        log_id = await repo.create(f"log {i}", make_analysis(), make_diagnosis())
        ids_in_order.append(log_id)
        await asyncio.sleep(0.01)  # garante timestamps distintos

    result = await repo.list_paginated(page=1, page_size=10)

    # O mais recente deve vir primeiro
    assert result[0].id == ids_in_order[-1]
    assert result[-1].id == ids_in_order[0]

    # Verifica que a ordem é decrescente
    for i in range(len(result) - 1):
        assert result[i].created_at >= result[i + 1].created_at
