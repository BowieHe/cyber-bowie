"""Unit tests for standalone nodes that do not require LLM mocks."""

import pytest

from cyber_persona.engine.nodes.error_handler import error_handling_node
from cyber_persona.models import create_default_state


@pytest.mark.asyncio
async def test_error_handling_node_with_missing_info():
    state = create_default_state()
    state["user_query"] = "Test query"
    state["missing_information"] = "缺少2026年最新持仓数据"
    state["search_retry_count"] = 3
    state["draft_retry_count"] = 0

    result = await error_handling_node(state)

    assert "final_answer" in result
    assert "missing2026年最新持仓数据" in result["final_answer"] or "缺少2026年最新持仓数据" in result["final_answer"]
    assert result.get("error") == "force_quit"


@pytest.mark.asyncio
async def test_error_handling_node_without_missing_info():
    state = create_default_state()
    state["user_query"] = "Test query"

    result = await error_handling_node(state)

    assert "final_answer" in result
    assert "无法生成满意的答复" in result["final_answer"] or "无法完整回答" in result["final_answer"]
    assert result.get("error") == "force_quit"
