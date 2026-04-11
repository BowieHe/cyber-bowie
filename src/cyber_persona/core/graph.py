"""LangGraph workflow with LLM node."""
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


def create_graph():
    """Create a graph with LLM node."""

    # Debug: print env vars (remove after fixing)
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.moonshot.cn/v1")
    model = os.getenv("OPENAI_MODEL", "kimi-k2.5")
    print(f"[DEBUG] API Key: {api_key[:20]}..." if api_key else "[DEBUG] API Key: None")
    print(f"[DEBUG] Base URL: {base_url}")
    print(f"[DEBUG] Model: {model}")

    # Initialize LLM with OpenAI compatible format (Kimi)
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "1")),
    )

    def process_input(state: dict) -> dict:
        """Process user input and prepare messages."""
        user_input = state.get("input", "")
        messages = state.get("messages", [])
        messages.append({"role": "user", "content": user_input})
        return {"messages": messages, "input": user_input}

    def llm_node(state: dict) -> dict:
        """Call LLM and get response."""
        messages = state.get("messages", [])

        # Convert to LangChain message format
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                from langchain_core.messages import HumanMessage
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                from langchain_core.messages import AIMessage
                lc_messages.append(AIMessage(content=msg["content"]))

        # Call LLM
        response = llm.invoke(lc_messages)
        content = response.content if hasattr(response, 'content') else str(response)

        messages.append({"role": "assistant", "content": content})
        return {
            "messages": messages,
            "output": content,
            "llm_response": content
        }

    def format_output(state: dict) -> dict:
        """Format final output."""
        llm_response = state.get("llm_response", "")
        return {
            "output": f"🤖 {llm_response}",
            "messages": state.get("messages", [])
        }

    builder = StateGraph(dict)
    builder.add_node("process_input", process_input)
    builder.add_node("llm", llm_node)
    builder.add_node("format_output", format_output)

    builder.set_entry_point("process_input")
    builder.add_edge("process_input", "llm")
    builder.add_edge("llm", "format_output")
    builder.add_edge("format_output", END)

    return builder.compile()
