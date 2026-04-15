"""FastAPI application factory."""

import logging

from fastapi import FastAPI

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

    # Register routes
    app.include_router(health_router)
    app.include_router(chat_router)

    return app
