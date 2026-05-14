"""Testes para a interface abstrata LogParser."""

from __future__ import annotations

from typing import List

import pytest

from src.models.schemas import LogEntry, LogTemplate
from src.parsers.base import LogParser


class ConcreteLogParser(LogParser):
    """Implementação concreta de LogParser para testes."""

    def parse(self, raw_content: str) -> List[LogEntry]:
        """Implementação simples para testes."""
        return []

    def get_templates(self) -> List[LogTemplate]:
        """Implementação simples para testes."""
        return []


class TestLogParserInterface:
    """Testes para a interface abstrata LogParser."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Propriedade: LogParser não pode ser instanciado diretamente."""
        with pytest.raises(TypeError):
            LogParser()  # type: ignore[abstract]

    def test_concrete_implementation_can_be_instantiated(self) -> None:
        """Propriedade: Implementação concreta pode ser instanciada."""
        parser = ConcreteLogParser()
        assert isinstance(parser, LogParser)

    def test_parse_method_exists(self) -> None:
        """Propriedade: Método parse existe e é chamável."""
        parser = ConcreteLogParser()
        assert hasattr(parser, "parse")
        assert callable(parser.parse)

    def test_get_templates_method_exists(self) -> None:
        """Propriedade: Método get_templates existe e é chamável."""
        parser = ConcreteLogParser()
        assert hasattr(parser, "get_templates")
        assert callable(parser.get_templates)

    def test_parse_returns_list_of_log_entries(self) -> None:
        """Propriedade: parse retorna List[LogEntry]."""
        parser = ConcreteLogParser()
        result = parser.parse("test content")
        assert isinstance(result, list)

    def test_get_templates_returns_list_of_templates(self) -> None:
        """Propriedade: get_templates retorna List[LogTemplate]."""
        parser = ConcreteLogParser()
        result = parser.get_templates()
        assert isinstance(result, list)

    def test_subclass_without_parse_raises_error(self) -> None:
        """Propriedade: Subclasse sem implementar parse gera erro."""

        class IncompleteParser(LogParser):
            def get_templates(self) -> List[LogTemplate]:
                return []

        with pytest.raises(TypeError):
            IncompleteParser()  # type: ignore[abstract]

    def test_subclass_without_get_templates_raises_error(self) -> None:
        """Propriedade: Subclasse sem implementar get_templates gera erro."""

        class IncompleteParser(LogParser):
            def parse(self, raw_content: str) -> List[LogEntry]:
                return []

        with pytest.raises(TypeError):
            IncompleteParser()  # type: ignore[abstract]

    def test_mypy_strict_compliance(self) -> None:
        """Propriedade: Interface é compatível com mypy --strict."""
        parser: LogParser = ConcreteLogParser()
        entries: List[LogEntry] = parser.parse("test")
        templates: List[LogTemplate] = parser.get_templates()

        assert isinstance(entries, list)
        assert isinstance(templates, list)
