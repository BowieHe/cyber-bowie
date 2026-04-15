"""Search executor node for the retriever agent."""

import logging
from typing import Any

from cyber_persona.models import AssistantState
from cyber_persona.tools import SearchTool

logger = logging.getLogger(__name__)


async def search_executor_node(state: AssistantState) -> dict[str, Any]:
    """Execute search using the async SearchTool.

    Reads the generated query from state (set by query_generator) and
    appends results to retrieved_context and attempted_queries.
    """
    query = state.get("current_query", "")
    if not query:
        logger.warning("SearchExecutor called without current_query")
        return {
            "retrieved_context": [],
            "attempted_queries": [],
            "status_message": "搜索执行失败：无搜索词",
        }

    logger.info("SearchExecutor running query=%r", query)

    # Use SearchTool with default config from settings
    tool = SearchTool()
    try:
        results = await tool.search(query)
        snippets: list[str] = []
        for item in results:
            text = f"[{item.title}] {item.snippet or ''}"
            if text.strip():
                snippets.append(text)

        logger.info("SearchExecutor got %d snippets for query=%r", len(snippets), query)
    except Exception as exc:
        logger.exception("SearchExecutor failed for query=%r", query)
        snippets = [f"搜索失败：{exc}"]
    finally:
        await tool.close()

    return {
        "retrieved_context": snippets,
        "attempted_queries": [query],
        "status_message": f"搜索完成，获取 {len(snippets)} 条结果",
    }
