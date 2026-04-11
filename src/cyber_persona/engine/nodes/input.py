"""Input processing node."""

from typing import Any

from cyber_persona.engine.nodes.base import BaseNode
from cyber_persona.models.message import Message


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

        return {
            **state,
            "messages": messages,
            "input_text": user_input,
        }
