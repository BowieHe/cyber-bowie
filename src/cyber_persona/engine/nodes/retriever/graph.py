"""Retriever Agent subgraph assembly."""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_openai import ChatOpenAI

from cyber_persona.engine.nodes.retriever.query_generator import query_generator_node
from cyber_persona.engine.nodes.retriever.search_executor import search_executor_node
from cyber_persona.models import AssistantState


def create_retriever_subgraph(
    llm: ChatOpenAI | None = None,
) -> CompiledStateGraph:
    """Build the retriever agent subgraph.

    Flow: query_generator -> search_executor -> END
    """
    builder = StateGraph(AssistantState)

    builder.add_node("query_generator", query_generator_node(llm))
    builder.add_node("search_executor", search_executor_node)

    builder.add_edge("query_generator", "search_executor")
    builder.add_edge("search_executor", END)

    builder.set_entry_point("query_generator")

    return builder.compile()
