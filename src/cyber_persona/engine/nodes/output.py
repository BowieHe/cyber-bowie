"""Output formatting node."""

import logging
from typing import Any

from cyber_persona.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)


class OutputNode(BaseNode):
    """Format final output for display."""

    def __init__(self, prefix: str = "🤖 ") -> None:
        super().__init__(name="format_output")
        self.prefix = prefix

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Format the final output."""
        llm_response = state.get("llm_response", "")
        formatted = f"{self.prefix}{llm_response}"

        logger.info("Formatted output: %r", formatted[:100])

        return {
            **state,
            "output": formatted,
            "current_node": self.name,
        }
