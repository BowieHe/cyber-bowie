"""FastAPI application factory."""

from fastapi import FastAPI

from cyber_persona.server.middleware import setup_cors
from cyber_persona.server.routes import health_router, chat_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
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
