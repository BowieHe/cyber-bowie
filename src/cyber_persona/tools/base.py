"""Base class for LangGraph tools."""

from abc import ABC, abstractmethod
from typing import Any, Callable
from langchain_core.tools import BaseTool


class ToolDefinition:
    """Definition for a tool that can be bound to LLM."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    def to_langchain_tool(self) -> BaseTool:
        """Convert to LangChain tool format."""
        # This is a placeholder for actual implementation
        # Would use @tool decorator or StructuredTool
        raise NotImplementedError("Tool conversion not yet implemented")


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_all_tools(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())

    def bind_to_llm(self, llm: Any) -> Any:
        """Bind all tools to an LLM instance."""
        # Placeholder: Would use llm.bind_tools() when tools are implemented
        return llm


# Global registry instance
tool_registry = ToolRegistry()
