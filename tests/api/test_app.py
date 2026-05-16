"""Testes para a aplicação FastAPI e injeção de dependências."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import get_settings


class TestCreateApp:
    """Testes para a factory create_app."""

    def test_creates_fastapi_instance(self) -> None:
        """Verifica que create_app retorna instância FastAPI configurada."""
        get_settings.cache_clear()
        app = create_app()
        assert app.title == "LogPulse IA"
        assert app.version == "0.1.0"

    def test_v1_router_registered(self) -> None:
        """Verifica que o router v1 está registrado com prefixo correto."""
        get_settings.cache_clear()
        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/api/v1/logs" in routes or any("/api/v1/logs" in r for r in routes)

    def test_openapi_schema_available(self) -> None:
        """Verifica que o schema OpenAPI está acessível."""
        get_settings.cache_clear()
        app = create_app()
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "LogPulse IA"

    def test_docs_endpoint_available(self) -> None:
        """Verifica que o Swagger UI está acessível."""
        get_settings.cache_clear()
        app = create_app()
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200
