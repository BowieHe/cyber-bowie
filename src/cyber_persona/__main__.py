"""Entry point for Cyber Persona CLI."""

import subprocess
import sys
import time

from cyber_persona.config import get_settings
from cyber_persona.server.app import create_app


def run_server():
    """Run the HTTP server."""
    import uvicorn

    settings = get_settings()
    app = create_app()

    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.server.log_level,
    )


def run_tui():
    """Run the TUI client."""
    from cyber_persona.client import ChatUI

    ui = ChatUI()
    ui.run()


def run_dev():
    """Run both server and TUI in dev mode."""
    print("🚀 Starting dev mode (server + TUI)...")
    print("   Press Ctrl+C to stop both\n")

    # Start server in subprocess
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "cyber_persona", "server"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # Wait for server to be ready
    time.sleep(2)

    try:
        # Start TUI in main process
        run_tui()
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        server_proc.terminate()
        server_proc.wait()
        print("✓ Dev mode stopped")


def print_usage():
    """Print usage information."""
    print("Usage: cp [server|tui|dev]")
    print("")
    print("Commands:")
    print("  server  - Start HTTP server only")
    print("  tui     - Start TUI client only (server must be running)")
    print("  dev     - Start both server and TUI")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "server":
        run_server()
    elif cmd == "tui":
        run_tui()
    elif cmd == "dev":
        run_dev()
    else:
        print(f"Unknown command: {cmd}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
