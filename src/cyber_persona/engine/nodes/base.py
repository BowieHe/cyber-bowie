"""Base node class for LangGraph nodes."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """Abstract base class for graph nodes."""

    def __init__(self, name: str, llm: ChatOpenAI | None = None) -> None:
        self.name = name
        self.llm = llm

    @abstractmethod
    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the node and return updated state."""
        pass

    def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Make node callable with logging."""
        logger.info("Executing node: %s", self.name)
        start = time.perf_counter()
        try:
            result = self.execute(state)
            elapsed = time.perf_counter() - start
            logger.info("Node %s finished in %.3fs", self.name, elapsed)
            return result
        except Exception:
            logger.exception("Node %s failed", self.name)
            raise
