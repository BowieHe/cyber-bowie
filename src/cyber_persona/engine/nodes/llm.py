"""LLM call node."""

from typing import Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from cyber_persona.engine.nodes.base import BaseNode
from cyber_persona.config import get_settings


class LLMNode(BaseNode):
    """Node for calling LLM and getting response."""

    def __init__(self, llm: ChatOpenAI | None = None) -> None:
        super().__init__(name="llm", llm=llm)

    def _get_or_create_llm(self) -> ChatOpenAI:
        """Get existing LLM or create new one from settings."""
        if self.llm:
            return self.llm

        settings = get_settings()
        return ChatOpenAI(
            model=settings.llm.model,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
            temperature=settings.llm.temperature,
        )

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list:
        """Convert dict messages to LangChain messages."""
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

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Call LLM and update state with response."""
        llm = self._get_or_create_llm()
        messages = state.get("messages", [])

        # Convert and call LLM
        lc_messages = self._convert_messages(messages)
        response = llm.invoke(lc_messages)

        # Extract content
        content = response.content if hasattr(response, "content") else str(response)

        # Add assistant message to history
        messages.append({"role": "assistant", "content": content})

        return {
            **state,
            "messages": messages,
            "llm_response": content,
            "output": content,
        }
