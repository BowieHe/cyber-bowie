"""Terminal UI using Rich."""

import httpx
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.tree import Tree

from cyber_persona.client.api.client import ChatClient, StreamEvent


class ChatUI:
    """Rich-based terminal chat UI."""

    def __init__(self, client: ChatClient | None = None) -> None:
        self.console = Console()
        self.client = client or ChatClient()
        self.nodes: dict[str, dict[str, Any]] = {}
        self.messages: list[dict[str, Any]] = []
        self._connected = False

    def print_welcome(self) -> None:
        """Print welcome message."""
        self.console.print("[green]✓ Connected to server[/green]\n")

    def print_goodbye(self) -> None:
        """Print goodbye message."""
        self.console.print("[green]✓ Goodbye![/green]")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[red]✗ {message}[/red]")

    def print_user(self, message: str) -> None:
        """Print user message."""
        self.console.print(f"[bold blue]User:[/bold blue] {message}")

    def print_ai(self, text: str, is_markdown: bool = False) -> None:
        """Print AI response."""
        self.console.print()
        if is_markdown:
            self.console.print(Markdown(text))
        else:
            self.console.print(f"[bold green]AI:[/bold green] {text}")
        self.console.print()

    def print_execution_tree(self) -> None:
        """Print execution flow tree."""
        if not self.nodes:
            return

        tree = Tree("[bold cyan]Execution Flow[/bold cyan]")
        for name, info in self.nodes.items():
            icon = "✅" if info["status"] == "done" else "⏳"
            node = tree.add(f"{icon} [bold]{name}[/] ({info['status']})")
            # Prefer status_message for concise display
            display_output = info.get("status_message") or info.get("output", "")
            if display_output:
                output = display_output[:60]
                if len(display_output) > 60:
                    output += "..."
                node.add(f"[dim]{output}[/dim]")
        self.console.print(tree)
        self.console.print()

    def update_node(self, name: str, status: str, output: str = "", status_message: str = "") -> None:
        """Update node status."""
        # Mark all previous nodes as done
        for n in self.nodes:
            self.nodes[n]["status"] = "done"
        self.nodes[name] = {
            "status": status,
            "output": output,
            "status_message": status_message,
        }

    def get_input(self) -> str:
        """Get user input."""
        return self.console.input("[bold blue]>>>[/bold blue] ").strip()

    def handle_event(self, event: StreamEvent) -> str:
        """Process stream event and return final output."""
        if event.type == "node_complete":
            node_data = event.data or {}
            self.update_node(
                event.node or "unknown",
                "running",
                node_data.get("output", ""),
                node_data.get("status_message", ""),
            )
            # Prefer final_answer for research path, fallback to output / llm_response
            return (
                node_data.get("final_answer")
                or node_data.get("llm_response")
                or node_data.get("output", "")
            )

        elif event.type == "error":
            self.print_error(f"Server error: {event.message or 'Unknown'}")
            raise RuntimeError(event.message or "Unknown server error")

        elif event.type == "done":
            for n in self.nodes:
                self.nodes[n]["status"] = "done"

        return ""

    def run_turn(self, user_input: str) -> str:
        """Run a single conversation turn."""
        # Reset nodes for new turn
        self.nodes = {}

        final_output = ""

        try:
            for event in self.client.chat(user_input, self.messages):
                output = self.handle_event(event)
                if output:
                    final_output = output

        except httpx.ConnectError:
            self.print_error("Cannot connect to server at localhost:8000")
            self.print_error("Make sure the server is running: uv run cp server")
            raise

        except Exception as e:
            self.print_error(f"Error: {e}")
            raise

        # Display results
        self.print_user(user_input)
        self.print_execution_tree()

        if not final_output.strip():
            self.print_error(
                "Server returned an empty response. Please retry or restart the server."
            )
        else:
            self.print_ai(final_output)

        # Save to message history
        self.messages.append({"role": "user", "content": user_input})
        if final_output.strip():
            self.messages.append({"role": "assistant", "content": final_output})

        return final_output

    def run(self) -> None:
        """Run the main chat loop."""
        # Check connection
        if not self.client.health_check():
            self.print_error("Cannot connect to server at localhost:8000")
            self.print_error("Make sure the server is running: uv run cp server")
            return

        self._connected = True
        self.print_welcome()

        try:
            while True:
                user_input = self.get_input()

                if not user_input:
                    continue

                if user_input in ("quit", "exit", "q"):
                    break

                try:
                    self.run_turn(user_input)
                except Exception:
                    # Error already printed, continue
                    continue

        except KeyboardInterrupt:
            pass
        finally:
            self.print_goodbye()


def main() -> None:
    """Entry point for TUI."""
    ui = ChatUI()
    ui.run()
