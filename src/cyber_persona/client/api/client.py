"""HTTP API client for chat server."""

import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Generator

import httpx


@dataclass
class StreamEvent:
    """Stream event from server."""

    type: str
    node: str | None = None
    data: dict[str, Any] | None = None
    message: str | None = None


class ChatClient:
    """Client for chat API."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/chat"

    def chat(
        self,
        message: str,
        messages: list[dict[str, Any]] | None = None,
    ) -> Generator[StreamEvent, None, None]:
        """Send chat message and stream events."""
        payload = {
            "message": message,
            "messages": messages or [],
        }

        with httpx.Client() as client:
            with client.stream(
                "POST",
                self.chat_url,
                json=payload,
                headers={"Accept": "text/event-stream"},
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue

                    data = json.loads(line[6:])  # Remove "data: " prefix
                    yield self._parse_event(data)

    async def chat_async(
        self,
        message: str,
        messages: list[dict[str, Any]] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Async version of chat."""
        payload = {
            "message": message,
            "messages": messages or [],
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.chat_url,
                json=payload,
                headers={"Accept": "text/event-stream"},
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data = json.loads(line[6:])
                    yield self._parse_event(data)

    def _parse_event(self, data: dict[str, Any]) -> StreamEvent:
        """Parse event data from server."""
        return StreamEvent(
            type=data.get("type", "unknown"),
            node=data.get("node"),
            data=data.get("data"),
            message=data.get("message"),
        )

    def health_check(self) -> bool:
        """Check if server is healthy."""
        try:
            with httpx.Client() as client:
                response = client.get(f"{self.base_url}/health", timeout=5.0)
                return response.status_code == 200
        except httpx.RequestError:
            return False
