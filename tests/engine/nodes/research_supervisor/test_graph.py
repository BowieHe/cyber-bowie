import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage

from cyber_persona.engine.nodes.research_supervisor.graph import create_research_orchestrator_subgraph


@pytest.mark.asyncio
async def test_research_orchestrator_exits_with_next_agent():
    # Patch all LLM-dependent nodes so the graph runs without external API
    from cyber_persona.engine.nodes.research_supervisor.plan import ResearchPlanOutput
    from cyber_persona.models import HarnessEvaluation

    fake_plan_llm = MagicMock()
    fake_plan_structured = AsyncMock()
    fake_plan_structured.ainvoke.return_value = ResearchPlanOutput(
        topics=["测试主题1"],
        reasoning="test",
    )
    fake_plan_llm.with_structured_output.return_value = fake_plan_structured

    fake_reflect_llm = MagicMock()
    fake_reflect_structured = AsyncMock()
    fake_reflect_structured.ainvoke.return_value = HarnessEvaluation(
        status="PASSED",
        reasoning="test",
        missing_information="",
        correction_directive="",
    )
    fake_reflect_llm.with_structured_output.return_value = fake_reflect_structured

    fake_search_agent = AsyncMock()
    fake_search_agent.ainvoke.return_value = {
        "messages": [AIMessage(content="mock summary")],
    }

    with patch(
        "cyber_persona.engine.nodes.research_supervisor.plan.ChatOpenAI",
        return_value=fake_plan_llm,
    ), patch(
        "cyber_persona.engine.nodes.research_supervisor.reflect.ChatOpenAI",
        return_value=fake_reflect_llm,
    ), patch(
        "cyber_persona.engine.nodes.research_supervisor.gather.create_search_agent",
        return_value=fake_search_agent,
    ):
        agent = create_research_orchestrator_subgraph()
        result = await agent.ainvoke({
            "user_query": "测试",
            "research_plan": ["测试主题1"],
            "gather_round": 0,
            "retrieved_context": [],
            "sub_agent_results": [],
        })
    assert "next_agent" in result
