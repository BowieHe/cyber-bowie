"""Tests for the unified LangGraph workflow."""

import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage

from cyber_persona.engine.builder import create_graph
from cyber_persona.models import create_default_state


@pytest.mark.asyncio
async def test_graph_compiles():
    """Test that the unified graph compiles successfully."""
    graph = create_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_routes_chat_request():
    fake_supervisor = AsyncMock()
    fake_supervisor.side_effect = [
        {
            "next_agent": "chat_agent",
            "messages": [AIMessage(content="你好！")],
            "status_message": "supervisor done",
        },
        {
            "next_agent": "synthesizer",
            "messages": [AIMessage(content="你好！")],
            "status_message": "supervisor finalize",
        },
    ]

    fake_chat_agent = AsyncMock()
    fake_chat_agent.return_value = {
        "messages": [AIMessage(content="你好！")],
        "output": "你好！",
        "next_agent": "supervisor",
        "status_message": "chat done",
    }

    with patch(
        "cyber_persona.engine.builder.create_supervisor_agent",
        return_value=fake_supervisor,
    ), patch(
        "cyber_persona.engine.builder.create_chat_agent",
        return_value=fake_chat_agent,
    ), patch(
        "cyber_persona.engine.builder.create_research_orchestrator_subgraph",
        return_value=AsyncMock(return_value={"messages": []}),
    ), patch(
        "cyber_persona.engine.builder.drafter_node",
        return_value=AsyncMock(return_value={"messages": [], "draft": ""}),
    ), patch(
        "cyber_persona.engine.builder.fact_check_harness_node",
        return_value=AsyncMock(return_value={"current_harness_status": "PASSED"}),
    ), patch(
        "cyber_persona.engine.builder.create_debater_subgraph",
        return_value=AsyncMock(return_value={"messages": [], "debate_log": []}),
    ), patch(
        "cyber_persona.engine.builder.synthesizer_node",
        return_value=AsyncMock(return_value={"messages": [AIMessage(content="Done")], "final_answer": "Done"}),
    ), patch(
        "cyber_persona.engine.builder.error_handling_node",
        return_value=AsyncMock(return_value={"error": "", "status_message": ""}),
    ):
        graph = create_graph()
        result = await graph.ainvoke({
            "user_query": "你好",
            "messages": [{"role": "human", "content": "你好"}],
        })
    assert "messages" in result or "output" in result
