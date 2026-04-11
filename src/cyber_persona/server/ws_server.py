"""SSE server for streaming responses."""
import json
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat_endpoint(request: Request):
    """Stream chat responses using SSE."""
    data = await request.json()
    message = data.get("message", "")
    messages = data.get("messages", [])

    from cyber_persona.core.graph import create_graph
    graph = create_graph()

    async def event_stream():
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
