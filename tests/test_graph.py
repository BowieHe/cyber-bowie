"""Tests for the unified LangGraph workflow."""

import pytest
from unittest.mock import patch

from cyber_persona.engine.builder import create_graph
from cyber_persona.models import create_default_state


@pytest.mark.asyncio
async def test_graph_compiles():
    """Test that the unified graph compiles successfully."""
    graph = create_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_chat_path():
    """Test that a simple greeting flows through the CHAT branch and produces output."""
    graph = create_graph()
    state = create_default_state()
    state["input"] = "hello"
    state["user_query"] = "hello"
    state["messages"] = []

    result = await graph.ainvoke(state)

    assert "output" in result
    assert result["output"] != ""
    # Intent should be classified as CHAT for a simple greeting
    assert result.get("intent") == "CHAT"


@pytest.mark.skip(reason="Full research path requires stable external LLM and is flaky under rate limits")
@pytest.mark.asyncio
async def test_research_path_skeleton():
    """Test that a research-style query enters the research branch and reaches the end.

    This test mocks the SearchTool to avoid requiring a live MCP server.
    It still exercises the full graph topology including the intent router,
    retriever subgraph, harness, drafter, fact-check, debater, and synthesizer.
    """
    graph = create_graph()
    state = create_default_state()
    state["input"] = "分析一下宁德时代最近的投资风险"
    state["user_query"] = "分析一下宁德时代最近的投资风险"
    state["messages"] = []

    with patch(
        "cyber_persona.engine.nodes.retriever.search_executor.SearchTool.search"
    ) as mock_search:
        mock_search.return_value = [
            type("Result", (), {
                "title": "宁德时代2025年报",
                "snippet": "营收增长20%，净利润增长15%。",
                "url": "http://example.com",
                "source": "测试来源",
                "published_at": None,
            })()
        ]

        result = await graph.ainvoke(state)

    # The graph should reach END and set final_answer
    assert "final_answer" in result
    assert result.get("intent") == "RESEARCH"
