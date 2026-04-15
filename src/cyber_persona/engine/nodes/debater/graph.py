"""Debater Agent subgraph assembly."""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI

from cyber_persona.engine.nodes.debater.red_team import red_team_node
from cyber_persona.engine.nodes.debater.blue_team import blue_team_node
from cyber_persona.models import AssistantState

MAX_DEBATE_ROUNDS = 3


def debater_router(state: AssistantState) -> str:
    """Route after each blue-team response.

    Returns:
        - "continue": start next round if under limit.
        - "finish": end debate and proceed to synthesis.
    """
    round_num = state.get("debate_round", 0)
    if round_num < MAX_DEBATE_ROUNDS:
        return "continue"
    return "finish"


def create_debater_subgraph(
    llm: ChatOpenAI | None = None,
) -> CompiledStateGraph:
    """Build the debater agent subgraph.

    Flow:
        red_team -> blue_team -> debater_router
        router: continue -> red_team
        router: finish -> END
    """
    builder = StateGraph(AssistantState)

    builder.add_node("red_team", red_team_node(llm))
    builder.add_node("blue_team", blue_team_node(llm))

    builder.add_edge("red_team", "blue_team")
    builder.add_conditional_edges(
        "blue_team",
        debater_router,
        {
            "continue": "red_team",
            "finish": END,
        },
    )

    builder.set_entry_point("red_team")

    return builder.compile()
