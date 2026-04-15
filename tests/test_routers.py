"""Tests for conditional edge routers."""

import pytest

from cyber_persona.engine.routers import (
    search_harness_router,
    fact_check_harness_router,
)
from cyber_persona.models import create_default_state


class TestSearchHarnessRouter:
    def test_passed_routes_to_draft(self):
        state = create_default_state()
        state["current_harness_status"] = "PASSED"
        assert search_harness_router(state) == "continue_to_draft"

    def test_partial_accept_routes_to_draft_with_warning(self):
        state = create_default_state()
        state["current_harness_status"] = "PARTIAL_ACCEPT"
        assert search_harness_router(state) == "continue_to_draft_with_warning"

    def test_needs_retry_under_limit(self):
        state = create_default_state()
        state["current_harness_status"] = "NEEDS_RETRY"
        state["search_retry_count"] = 1
        assert search_harness_router(state) == "rewrite_search_query"

    def test_needs_retry_at_limit(self):
        state = create_default_state()
        state["current_harness_status"] = "NEEDS_RETRY"
        state["search_retry_count"] = 3
        assert search_harness_router(state) == "force_quit"

    def test_needs_retry_over_limit(self):
        state = create_default_state()
        state["current_harness_status"] = "NEEDS_RETRY"
        state["search_retry_count"] = 5
        assert search_harness_router(state) == "force_quit"

    def test_unexpected_status_force_quit(self):
        state = create_default_state()
        state["current_harness_status"] = "UNKNOWN"
        assert search_harness_router(state) == "force_quit"


class TestFactCheckHarnessRouter:
    def test_passed_routes_to_debate(self):
        state = create_default_state()
        state["current_harness_status"] = "PASSED"
        assert fact_check_harness_router(state) == "continue_to_debate"

    def test_needs_retry_under_limit(self):
        state = create_default_state()
        state["current_harness_status"] = "NEEDS_RETRY"
        state["draft_retry_count"] = 2
        assert fact_check_harness_router(state) == "rewrite_draft"

    def test_needs_retry_at_limit(self):
        state = create_default_state()
        state["current_harness_status"] = "NEEDS_RETRY"
        state["draft_retry_count"] = 3
        assert fact_check_harness_router(state) == "force_quit"

    def test_unexpected_status_force_quit(self):
        state = create_default_state()
        state["current_harness_status"] = "BOGUS"
        assert fact_check_harness_router(state) == "force_quit"
