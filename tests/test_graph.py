"""Tests for LangGraph workflow."""
import pytest
from cyber_persona.core.graph import create_graph


@pytest.mark.asyncio
async def test_graph_execution():
    """Test that the graph executes successfully."""
    graph = create_graph()
    result = await graph.ainvoke({"input": "hello"})

    assert "output" in result
    assert "Step B finalized" in result["output"]


@pytest.mark.asyncio
async def test_graph_streaming():
    """Test that the graph streams node events."""
    graph = create_graph()
    events = []

    async for event in graph.astream({"input": "test"}):
        events.append(event)

    assert len(events) == 2
    # First event should be from step_a
    assert "step_a" in str(events[0])
    # Second event should be from step_b
    assert "step_b" in str(events[1])
