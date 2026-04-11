"""Dependency injection for FastAPI."""

from functools import lru_cache
from typing import AsyncGenerator

from langgraph.graph import StateGraph

from cyber_persona.config import get_settings
from cyber_persona.engine import create_graph


@lru_cache()
def get_graph() -> StateGraph:
    """Get or create cached graph instance."""
    return create_graph()


async def get_graph_async() -> AsyncGenerator[StateGraph, None]:
    """Async dependency for graph instance."""
    yield get_graph()
