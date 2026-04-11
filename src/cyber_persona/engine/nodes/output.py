"""Output formatting node."""

from typing import Any

from cyber_persona.engine.nodes.base import BaseNode


class OutputNode(BaseNode):
    """Format final output for display."""

    def __init__(self, prefix: str = "🤖 ") -> None:
        super().__init__(name="format_output")
        self.prefix = prefix

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Format the final output."""
        llm_response = state.get("llm_response", "")
        formatted = f"{self.prefix}{llm_response}"

        return {
            **state,
            "output": formatted,
        }
