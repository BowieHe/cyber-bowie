"""Tests for Retriever and Debater subgraph compilation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cyber_persona.engine.nodes.retriever.graph import create_retriever_subgraph
from cyber_persona.engine.nodes.debater.graph import create_debater_subgraph
from cyber_persona.models import create_default_state


@pytest.mark.asyncio
async def test_retriever_subgraph_compiles():
    """Verify the retriever subgraph can be compiled."""
    subgraph = create_retriever_subgraph()
    assert subgraph is not None


@pytest.mark.asyncio
async def test_retriever_subgraph_runs_with_mock_search():
    """Run the retriever subgraph with mocked LLM and search tool.

    This test does not require an external API key or network access.
    """
    fake_query = "mocked query"
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(
        return_value=type("QueryOutput", (), {"query": fake_query, "reasoning": "test"})()
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    subgraph = create_retriever_subgraph(llm=mock_llm)
    state = create_default_state()
    state["user_query"] = "test query"
    state["attempted_queries"] = []

    with patch(
        "cyber_persona.engine.nodes.retriever.search_executor.SearchTool.search"
    ) as mock_search:
        mock_search.return_value = [
            type("Result", (), {
                "title": "Mock Result",
                "snippet": "This is a mock search result.",
                "url": "http://example.com",
                "source": "Mock",
                "published_at": None,
            })()
        ]

        result = await subgraph.ainvoke(state)

    assert "retrieved_context" in result
    assert len(result["retrieved_context"]) > 0
    assert fake_query in result["attempted_queries"]


@pytest.mark.asyncio
async def test_debater_subgraph_compiles():
    """Verify the debater subgraph can be compiled."""
    subgraph = create_debater_subgraph()
    assert subgraph is not None


@pytest.mark.asyncio
async def test_debater_subgraph_exits_after_max_rounds():
    """Verify the debater loop exits after MAX_DEBATE_ROUNDS.

    We inject a mock LLM so the test does not require an external API.
    """
    fake_response = type("FakeResponse", (), {"content": "Mocked debate content."})()
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = fake_response

    subgraph = create_debater_subgraph(llm=mock_llm)
    state = create_default_state()
    state["draft"] = "Dummy draft for testing debate loop."
    state["debate_round"] = 0
    state["debate_log"] = []

    result = await subgraph.ainvoke(state)

    # The loop should have run red_team and blue_team 3 times each
    debate_log = result.get("debate_log", [])
    assert len(debate_log) >= 6, f"Expected at least 6 debate entries, got {len(debate_log)}"
    assert result.get("debate_round", 0) == 3, f"Expected debate_round=3, got {result.get('debate_round')}"
