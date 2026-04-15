"""Conditional edge routers for the research graph."""

import logging

from cyber_persona.models import AssistantState

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def search_harness_router(state: AssistantState) -> str:
    """Route after search harness evaluation.

    Returns:
        - "continue_to_draft": information is sufficient.
        - "continue_to_draft_with_warning": partial acceptance.
        - "rewrite_search_query": needs retry (and under limit).
        - "force_quit": retry limit reached or unexpected state.
    """
    status = state.get("current_harness_status", "")
    retry_count = state.get("search_retry_count", 0)

    logger.info("SearchHarnessRouter status=%s retry=%d", status, retry_count)

    if status == "PASSED":
        return "continue_to_draft"

    if status == "PARTIAL_ACCEPT":
        return "continue_to_draft_with_warning"

    if status == "NEEDS_RETRY":
        if retry_count >= MAX_RETRIES:
            logger.warning("Search retry limit reached (%d), forcing quit", retry_count)
            return "force_quit"
        return "rewrite_search_query"

    logger.error("Unexpected harness status=%r, forcing quit", status)
    return "force_quit"


def fact_check_harness_router(state: AssistantState) -> str:
    """Route after fact-check harness evaluation.

    Returns:
        - "continue_to_debate": draft passes fact check.
        - "rewrite_draft": needs retry (and under limit).
        - "force_quit": retry limit reached or unexpected state.
    """
    status = state.get("current_harness_status", "")
    retry_count = state.get("draft_retry_count", 0)

    logger.info("FactCheckHarnessRouter status=%s retry=%d", status, retry_count)

    if status == "PASSED":
        return "continue_to_debate"

    if status == "NEEDS_RETRY":
        if retry_count >= MAX_RETRIES:
            logger.warning("Draft retry limit reached (%d), forcing quit", retry_count)
            return "force_quit"
        return "rewrite_draft"

    logger.error("Unexpected harness status=%r, forcing quit", status)
    return "force_quit"
