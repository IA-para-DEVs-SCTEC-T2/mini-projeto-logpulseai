"""Testes para a aplicação FastAPI principal do LogPulse IA.

Cobre: criação da app, CORS, routers, docs, redoc, health check e middleware.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Limpa o cache de settings antes de cada teste."""
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """TestClient com a aplicação criada."""
    return TestClient(create_app())


class TestCreateApp:
    """Testes para a factory create_app."""

    def test_cria_instancia_fastapi(self, client: TestClient) -> None:
        """create_app retorna instância FastAPI configurada."""
        app = create_app()
        assert app.title == "LogPulse IA"
        assert app.version == "0.1.0"

    def test_router_v1_registrado(self, client: TestClient) -> None:
        """Router v1 está registrado com prefixo /api/v1."""
        app = create_app()
        routes = [r.path for r in app.routes]
        assert any("/api/v1/logs" in r for r in routes)

    def test_debug_desabilitado_por_padrao(self) -> None:
        """debug=False por padrão."""
        app = create_app()
        assert app.debug is False


class TestDocumentacao:
    """Testes para endpoints de documentação."""

    def test_swagger_ui_acessivel(self, client: TestClient) -> None:
        """Swagger UI está acessível em /docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_acessivel(self, client: TestClient) -> None:
        """ReDoc está acessível em /redoc."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_acessivel(self, client: TestClient) -> None:
        """Schema OpenAPI está acessível em /openapi.json."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "LogPulse IA"

    def test_openapi_contem_endpoints_de_logs(self, client: TestClient) -> None:
        """Schema OpenAPI contém os endpoints de logs."""
        response = client.get("/openapi.json")
        paths = response.json()["paths"]
        assert any("/api/v1/logs" in p for p in paths)


class TestCORS:
    """Testes para configuração de CORS."""

    def test_cors_headers_presentes_em_preflight(self, client: TestClient) -> None:
        """Resposta OPTIONS contém headers CORS."""
        response = client.options(
            "/api/v1/logs",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers

    def test_cors_permite_qualquer_origem(self, client: TestClient) -> None:
        """CORS permite qualquer origem (*)."""
        response = client.get(
            "/health",
            headers={"Origin": "http://qualquer-origem.com"},
        )
        assert response.headers.get("access-control-allow-origin") == "*"


class TestHealthCheck:
    """Testes para o endpoint GET /health."""

    def test_health_retorna_200(self, client: TestClient) -> None:
        """GET /health retorna HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_retorna_json_com_status(self, client: TestClient) -> None:
        """GET /health retorna JSON com campo status."""
        response = client.get("/health")
        body = response.json()
        assert "status" in body
        assert body["status"] in ("healthy", "degraded")

    def test_health_retorna_componentes(self, client: TestClient) -> None:
        """GET /health retorna detalhes de cada componente."""
        response = client.get("/health")
        body = response.json()
        assert "components" in body
        components = body["components"]
        assert "api" in components
        assert "database" in components
        assert "ollama" in components

    def test_health_api_sempre_healthy(self, client: TestClient) -> None:
        """Componente 'api' é sempre healthy."""
        response = client.get("/health")
        assert response.json()["components"]["api"]["status"] == "healthy"

    def test_health_cada_componente_tem_status(self, client: TestClient) -> None:
        """Cada componente tem campo 'status'."""
        response = client.get("/health")
        for name, component in response.json()["components"].items():
            assert "status" in component, f"Componente '{name}' sem campo status"


class TestMiddlewareErros:
    """Testes para o middleware de tratamento de erros integrado na app."""

    def test_rota_inexistente_retorna_404(self, client: TestClient) -> None:
        """Rota inexistente retorna HTTP 404."""
        response = client.get("/rota-que-nao-existe")
        assert response.status_code == 404
