"""Zectrix API client."""

import logging

import httpx

from cyber_persona.plugins.zectrix.config import ZECTRIX_API_KEY, ZECTRIX_BASE_URL, ZECTRIX_DEVICE_ID
from cyber_persona.plugins.zectrix.models import Device, DisplayPushResult, Todo

logger = logging.getLogger(__name__)


class ZectrixClient:
    """HTTP client for Zectrix Open API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or ZECTRIX_API_KEY
        self.base_url = (base_url or ZECTRIX_BASE_URL).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"X-API-Key": self.api_key},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "ZectrixClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def list_devices(self) -> list[Device]:
        """GET /devices — list all bound devices."""
        resp = await self.client.get(f"{self.base_url}/devices")
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))
        return [Device.model_validate(d) for d in data.get("data", [])]

    async def get_first_device_id(self) -> str:
        """Return the first device's ID, or fall back to env var."""
        devices = await self.list_devices()
        if devices:
            return devices[0].deviceId
        if ZECTRIX_DEVICE_ID:
            return ZECTRIX_DEVICE_ID
        raise ZectrixAPIError("No device found and ZECTRIX_DEVICE_ID not set")

    # ── Todos ───────────────────────────────────────────────

    async def list_todos(
        self,
        *,
        status: int | None = None,
        device_id: str | None = None,
    ) -> list[Todo]:
        """GET /todos — list todos with optional filters."""
        params: dict[str, str] = {}
        if status is not None:
            params["status"] = str(status)
        if device_id:
            params["deviceId"] = device_id
        resp = await self.client.get(f"{self.base_url}/todos", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))
        return [Todo.model_validate(t) for t in data.get("data", [])]

    async def create_todo(self, todo: Todo) -> Todo:
        """POST /todos — create a new todo."""
        resp = await self.client.post(
            f"{self.base_url}/todos",
            json=todo.model_dump(exclude_none=True),
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))
        return Todo.model_validate(data["data"])

    async def update_todo(self, todo_id: int, todo: Todo) -> Todo:
        """PUT /todos/{id} — update a todo."""
        payload = todo.model_dump(exclude_none=True)
        # ID is path param, not body
        payload.pop("id", None)
        resp = await self.client.put(
            f"{self.base_url}/todos/{todo_id}",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))
        return Todo.model_validate(data["data"])

    async def toggle_complete(self, todo_id: int) -> None:
        """PUT /todos/{id}/complete — toggle completion status."""
        resp = await self.client.put(f"{self.base_url}/todos/{todo_id}/complete")
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))

    async def delete_todo(self, todo_id: int) -> None:
        """DELETE /todos/{id} — delete a todo."""
        resp = await self.client.delete(f"{self.base_url}/todos/{todo_id}")
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))

    # ── Display push ────────────────────────────────────────

    async def push_text(
        self,
        device_id: str,
        text: str,
        font_size: int = 20,
        page_id: str = "1",
    ) -> DisplayPushResult:
        """POST /devices/{deviceId}/display/text — push plain text."""
        resp = await self.client.post(
            f"{self.base_url}/devices/{device_id}/display/text",
            json={"text": text, "fontSize": font_size, "pageId": page_id},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))
        return DisplayPushResult.model_validate(data["data"])

    async def push_structured_text(
        self,
        device_id: str,
        title: str,
        body: str,
        page_id: str = "1",
    ) -> DisplayPushResult:
        """POST /devices/{deviceId}/display/structured-text — push title + body."""
        resp = await self.client.post(
            f"{self.base_url}/devices/{device_id}/display/structured-text",
            json={"title": title, "body": body, "pageId": page_id},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))
        return DisplayPushResult.model_validate(data["data"])

    async def delete_page(
        self,
        device_id: str,
        page_id: str | None = None,
    ) -> None:
        """DELETE /devices/{deviceId}/display/pages/{pageId} — delete a page."""
        url = f"{self.base_url}/devices/{device_id}/display/pages"
        if page_id:
            url = f"{url}/{page_id}"
        resp = await self.client.delete(url)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ZectrixAPIError(data.get("msg", "Unknown error"))


class ZectrixAPIError(Exception):
    """Zectrix API returned an error."""
