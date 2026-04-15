import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage, ToolMessage

from cyber_persona.engine.nodes.supervisor import create_supervisor_agent


@pytest.mark.asyncio
async def test_supervisor_decides_chat():
    fake_agent = AsyncMock()
    fake_agent.ainvoke.return_value = {
        "messages": [
            ToolMessage(content="chat_agent", tool_call_id="tc_1", name="handoff_to_chat_agent"),
        ],
    }

    with patch(
        "cyber_persona.engine.nodes.supervisor.create_react_agent",
        return_value=fake_agent,
    ):
        agent = create_supervisor_agent()
        result = await agent({
            "user_query": "你好",
            "messages": [{"role": "human", "content": "你好"}],
        })
    assert "next_agent" in result
    assert result["next_agent"] in ["chat_agent", "research_orchestrator", "drafter", "debater_agent", "synthesizer"]
