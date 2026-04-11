"""Base node class for LangGraph nodes."""

from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI


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
        """Make node callable."""
        return self.execute(state)
