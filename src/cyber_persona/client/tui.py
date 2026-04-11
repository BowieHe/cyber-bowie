"""Simple CLI client with Rich formatting using SSE."""
import json
import sys

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.tree import Tree


class ChatUI:
    """Simple chat UI with Rich formatting."""

    def __init__(self):
        self.console = Console()
        self.nodes = {}
        self.messages = []

    def print_tree(self, user_input: str):
        """Print execution tree for current turn."""
        self.console.print(f"[bold blue]User:[/bold blue] {user_input}")

        if self.nodes:
            tree = Tree("[bold cyan]Execution Flow[/bold cyan]")
            for name, info in self.nodes.items():
                icon = "✅" if info["status"] == "done" else "⏳"
                node = tree.add(f"{icon} [bold]{name}[/] ({info['status']})")
                if "output" in info:
                    output = info["output"][:60]
                    if len(info["output"]) > 60:
                        output += "..."
                    node.add(f"[dim]{output}[/dim]")
            self.console.print(tree)

    def update_node(self, name: str, status: str, output: str = ""):
        """Update node status."""
        for n in self.nodes:
            self.nodes[n]["status"] = "done"
        self.nodes[name] = {"status": status, "output": output}

    def print_ai(self, text: str, is_markdown: bool = False):
        """Print AI response."""
        if is_markdown:
            self.console.print(Markdown(text))
        else:
            self.console.print(f"[bold green]AI:[/bold green] {text}")
        self.console.print()

    def input(self) -> str:
        """Get user input."""
        return self.console.input("[bold blue]>>>[/bold blue] ").strip()


def main():
    ui = ChatUI()
    url = "http://localhost:8000/chat"

    ui.console.print("[green]✓ Connected to server[/green]\n")

    while True:
        user_input = ui.input()

        if not user_input:
            continue

        if user_input in ("quit", "exit", "q"):
            ui.console.print("[green]✓ Goodbye![/green]")
            break

        # Reset nodes for new turn
        ui.nodes = {}

        try:
            with httpx.Client() as client:
                with client.stream(
                    "POST",
                    url,
                    json={"message": user_input, "messages": ui.messages},
                    headers={"Accept": "text/event-stream"},
                    timeout=60.0
                ) as response:
                    response.raise_for_status()

                    final_output = ""

                    for line in response.iter_lines():
                        if not line.startswith("data: "):
                            continue

                        data = json.loads(line[6:])  # Remove "data: " prefix

                        if data["type"] == "node_complete":
                            ui.update_node(
                                data["node"],
                                "running",
                                data["data"].get("output", "")
                            )
                            final_output = data["data"].get("llm_response", data["data"].get("output", ""))

                        elif data["type"] == "error":
                            ui.console.print(f"[red]Server error: {data.get('message', 'Unknown')}[/red]")
                            break

                        elif data["type"] == "done":
                            for n in ui.nodes:
                                ui.nodes[n]["status"] = "done"
                            break

            # Display results
            ui.print_tree(user_input)
            ui.print_ai(final_output)

            # Save to message history
            ui.messages.append({"role": "user", "content": user_input})
            ui.messages.append({"role": "assistant", "content": final_output})

        except httpx.ConnectError:
            ui.console.print("[red]✗ Cannot connect to server at localhost:8000[/red]")
            ui.console.print("  Make sure the server is running: uv run cp server")
        except Exception as e:
            ui.console.print(f"[red]✗ Error: {e}[/red]")


if __name__ == "__main__":
    main()
