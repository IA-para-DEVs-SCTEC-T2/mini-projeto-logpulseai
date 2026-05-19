"""Re-export para compatibilidade — use src.api.v1.routes.logs_routes."""

from src.api.v1.routes.logs_routes import router  # noqa: F401

__all__ = ["router"]
