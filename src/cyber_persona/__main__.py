"""Entry point for Cyber Persona CLI."""

import multiprocessing
import signal
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
    """Run TUI and server together. Server stops when TUI exits."""
    # Ignore SIGINT in parent so it propagates cleanly to children
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    process = multiprocessing.Process(target=run_server)
    process.start()

    # Wait briefly for server to come up before launching TUI
    time.sleep(0.5)

    try:
        run_tui()
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()


def print_usage():
    """Print usage information."""
    print("Usage: cp [server|tui|dev]")
    print("")
    print("Commands:")
    print("  server  - Start HTTP server only")
    print("  tui     - Start TUI client only (server must be running)")
    print("  dev     - Start both server and TUI (server stops on exit)")


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
