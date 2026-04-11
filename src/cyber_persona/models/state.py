"""Graph state definition."""

from dataclasses import dataclass, field
from typing import Any

from cyber_persona.models.message import Message


@dataclass
class GraphState:
    """State object passed between LangGraph nodes."""

    # Input
    input_text: str = ""

    # Conversation history
    messages: list[Message] = field(default_factory=list)

    # Current processing
    current_node: str = ""
    node_outputs: dict[str, Any] = field(default_factory=dict)

    # LLM response
    llm_response: str = ""

    # Tool calls (for future tool support)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: dict[str, Any] = field(default_factory=dict)

    # Output
    output: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for LangGraph."""
        return {
            "input": self.input_text,
            "messages": [m.to_dict() for m in self.messages],
            "current_node": self.current_node,
            "node_outputs": self.node_outputs,
            "llm_response": self.llm_response,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "output": self.output,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphState":
        """Create from dictionary."""
        messages = [
            Message.from_dict(m) for m in data.get("messages", [])
        ]
        return cls(
            input_text=data.get("input", ""),
            messages=messages,
            current_node=data.get("current_node", ""),
            node_outputs=data.get("node_outputs", {}),
            llm_response=data.get("llm_response", ""),
            tool_calls=data.get("tool_calls", []),
            tool_results=data.get("tool_results", {}),
            output=data.get("output", ""),
            error=data.get("error"),
        )