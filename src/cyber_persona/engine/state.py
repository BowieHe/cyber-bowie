"""State management utilities."""

from typing import Any

from cyber_persona.models.state import GraphState


class StateManager:
    """Manage graph state transitions."""

    @staticmethod
    def create_initial_state(input_text: str, messages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Create initial state for graph execution."""
        from cyber_persona.models.message import Message

        state = GraphState(input_text=input_text)

        # Convert message dicts to Message objects
        if messages:
            state.messages = [Message.from_dict(m) for m in messages]

        return state.to_dict()

    @staticmethod
    def update_node_output(state: dict[str, Any], node_name: str, output: Any) -> dict[str, Any]:
        """Update output for a specific node."""
        if "node_outputs" not in state:
            state["node_outputs"] = {}
        state["node_outputs"][node_name] = output
        state["current_node"] = node_name
        return state

    @staticmethod
    def set_error(state: dict[str, Any], error: str) -> dict[str, Any]:
        """Set error state."""
        state["error"] = error
        return state

    @staticmethod
    def get_llm_messages(state: dict[str, Any]) -> list:
        """Get messages in LangChain format."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        messages = state.get("messages", [])
        lc_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        return lc_messages
