"""Error handling node for graceful degradation."""

import logging
from typing import Any

from cyber_persona.models import AssistantState

logger = logging.getLogger(__name__)


async def error_handling_node(state: AssistantState) -> dict[str, Any]:
    """Generate a graceful fallback response when retries are exhausted.

    This node is the final destination for 'force_quit' routing paths.
    """
    user_query = state.get("user_query", "")
    missing_info = state.get("missing_information", "")
    search_retry = state.get("search_retry_count", 0)
    draft_retry = state.get("draft_retry_count", 0)

    logger.warning(
        "ErrorHandling triggered: query=%r search_retries=%d draft_retries=%d",
        user_query,
        search_retry,
        draft_retry,
    )

    if missing_info:
        final_answer = (
            f"基于现有公开数据，系统无法完整回答您的问题。\n\n"
            f"目前缺失的关键信息包括：{missing_info}\n\n"
            f"建议您可以尝试补充更具体的查询条件，或等待相关数据披露后再做深入分析。"
        )
    else:
        final_answer = (
            "很抱歉，系统在多次尝试后仍无法生成满意的答复。"
            "可能是当前公开信息不足，或问题超出了系统的处理范围。"
            "请您稍后重试，或换个角度提问。"
        )

    return {
        "final_answer": final_answer,
        "output": final_answer,
        "status_message": "系统已触发兜底保护机制",
        "error": "force_quit",
    }
