"""Graph builder for creating LangGraph workflows."""

from typing import Any

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from cyber_persona.engine.nodes.input import InputNode
from cyber_persona.engine.nodes.llm import LLMNode
from cyber_persona.engine.nodes.output import OutputNode


def create_default_state() -> dict[str, Any]:
    """Create default state structure."""
    return {
        "input": "",
        "messages": [],
        "current_node": "",
        "node_outputs": {},
        "llm_response": "",
        "output": "",
        "error": None,
    }


class GraphBuilder:
    """Builder for creating LangGraph instances."""

    def __init__(self, llm: ChatOpenAI | None = None) -> None:
        self.llm = llm
        self.nodes: dict[str, Any] = {}
        self.edges: list[tuple[str, str]] = []
        self.entry_point: str = ""

    def add_node(self, name: str, node: Any) -> "GraphBuilder":
        """Add a node to the graph."""
        self.nodes[name] = node
        return self

    def add_edge(self, from_node: str, to_node: str) -> "GraphBuilder":
        """Add an edge between nodes."""
        self.edges.append((from_node, to_node))
        return self

    def set_entry_point(self, name: str) -> "GraphBuilder":
        """Set the entry point node."""
        self.entry_point = name
        return self

    def build(self) -> StateGraph:
        """Build and compile the graph."""
        # Create state graph with default state
        builder = StateGraph(dict)

        # Add nodes
        for name, node in self.nodes.items():
            builder.add_node(name, node)

        # Add edges
        for from_node, to_node in self.edges:
            if to_node == END:
                builder.add_edge(from_node, END)
            else:
                builder.add_edge(from_node, to_node)

        # Set entry point
        if self.entry_point:
            builder.set_entry_point(self.entry_point)

        return builder.compile()

    @classmethod
    def create_default(cls, llm: ChatOpenAI | None = None) -> StateGraph:
        """Create default graph with input -> llm -> output flow."""
        builder = cls(llm)

        # Add nodes
        builder.add_node("process_input", InputNode())
        builder.add_node("llm", LLMNode(llm))
        builder.add_node("format_output", OutputNode())

        # Add edges
        builder.add_edge("process_input", "llm")
        builder.add_edge("llm", "format_output")
        builder.add_edge("format_output", END)

        # Set entry point
        builder.set_entry_point("process_input")

        return builder.build()


# Convenience function
def create_graph(llm: ChatOpenAI | None = None) -> StateGraph:
    """Create default graph instance."""
    return GraphBuilder.create_default(llm)
