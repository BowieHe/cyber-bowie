import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage

from cyber_persona.engine.nodes.research_sub_agent.graph import create_search_agent


@pytest.mark.asyncio
async def test_search_agent_compiles_and_runs():
    fake_graph = AsyncMock()
    fake_graph.ainvoke.return_value = {
        "messages": [AIMessage(content="Mocked summary.")],
    }

    with patch(
        "cyber_persona.engine.nodes.research_sub_agent.graph.create_react_agent",
        return_value=fake_graph,
    ):
        agent = create_search_agent()
        result = await agent.ainvoke({
            "user_query": "宁德时代",
            "current_query": "宁德时代主营业务",
            "retrieved_context": [],
            "sub_agent_results": [],
        })
    assert "messages" in result
