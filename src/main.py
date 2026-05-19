"""Ponto de entrada para execução direta com uvicorn.

Uso:
    uvicorn src.api.app:app --reload --port 8000

Ou diretamente:
    python -m src.main
"""

from src.api.app import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
