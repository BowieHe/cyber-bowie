"""FastAPI application factory."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cyber_persona.server.middleware import setup_cors
from cyber_persona.server.routes import health_router, chat_router


def _setup_logging() -> None:
    """Configure logging for the cyber_persona namespace.

    This is called explicitly because uvicorn overrides basicConfig,
    so we attach a handler directly to our namespace logger.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger = logging.getLogger("cyber_persona")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(handler)


def _get_static_dir() -> Path | None:
    """Locate the built frontend static files directory."""
    # Try relative to this file: src/cyber_persona/server/app.py → web/dist
    candidate = Path(__file__).parent.parent.parent.parent / "web" / "dist"
    if candidate.exists() and candidate.is_dir():
        return candidate
    return None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    _setup_logging()

    app = FastAPI(
        title="Cyber Persona API",
        description="Multi-persona AI agent system",
        version="0.1.0",
    )

    # Setup middleware
    setup_cors(app)

    # Register API routes (must be before static files)
    app.include_router(health_router)
    app.include_router(chat_router)

    # Serve frontend static files if built
    static_dir = _get_static_dir()
    if static_dir is not None:
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
