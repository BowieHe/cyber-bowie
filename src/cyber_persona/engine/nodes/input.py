"""Input processing node."""

import logging
from typing import Any

from cyber_persona.engine.nodes.base import BaseNode
from cyber_persona.models.message import Message

logger = logging.getLogger(__name__)


class InputNode(BaseNode):
    """Process user input and prepare messages."""

    def __init__(self) -> None:
        super().__init__(name="process_input")

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Process user input and update state."""
        user_input = state.get("input", "")

        # Add user message to history
        messages = state.get("messages", [])
        messages.append({"role": "user", "content": user_input})

        logger.info("Input received: %r | Total messages: %d", user_input, len(messages))

        return {
            **state,
            "messages": messages,
            "input_text": user_input,
            "current_node": self.name,
        }
