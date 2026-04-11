"""Chat endpoints."""

import json
import traceback
from typing import Any

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from langgraph.graph import StateGraph

from cyber_persona.server.deps import get_graph

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat_endpoint(
    request: Request,
    graph: StateGraph = Depends(get_graph),
) -> StreamingResponse:
    """Stream chat responses using SSE."""
    data = await request.json()
    message = data.get("message", "")
    messages = data.get("messages", [])

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in graph.astream({"input": message, "messages": messages}):
                node_name = list(event.keys())[0]
                node_data = list(event.values())[0]

                yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name, 'data': node_data})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
