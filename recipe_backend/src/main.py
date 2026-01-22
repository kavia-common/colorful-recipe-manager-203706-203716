"""
Backend service entrypoint.

Some runtimes expect an ASGI app at `src/main.py` (e.g. `uvicorn src.main:app`).
This module re-exports the FastAPI `app` defined in `src/api/main.py` to ensure
the deployed server loads the correct routes (including /recipes CRUD).
"""

from src.api.main import app  # noqa: F401
