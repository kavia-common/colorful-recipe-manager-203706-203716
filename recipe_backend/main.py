"""
Backend service root entrypoint (compatibility shim).

Some deployment environments default to importing an ASGI app from `main.py`
at the repository root (e.g. `uvicorn main:app`).

This module re-exports the FastAPI `app` defined in `src/api/main.py` to ensure
the deployed server loads the correct routes (including /recipes CRUD).
"""

from src.api.main import app  # noqa: F401
