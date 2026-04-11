"""Message models for conversation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """A single message in the conversation."""

    role: MessageRole
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    name: str | None = None  # For tool messages

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            role=MessageRole(data.get("role", "user")),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            name=data.get("name"),
        )

    @classmethod
    def user(cls, content: str) -> "Message":
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)

    @classmethod
    def system(cls, content: str) -> "Message":
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def tool(cls, content: str, name: str) -> "Message":
        """Create a tool message."""
        return cls(role=MessageRole.TOOL, content=content, name=name)