"""Entry point for Cyber Persona CLI."""

import multiprocessing
import signal
import sys
import time
import webbrowser

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


def run_dev():
    """Run server and auto-open browser. Server stops on interrupt."""
    # Ignore SIGINT in parent so it propagates cleanly to children
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    process = multiprocessing.Process(target=run_server)
    process.start()

    # Wait briefly for server to come up before opening browser
    time.sleep(0.8)

    settings = get_settings()
    url = f"http://localhost:{settings.server.port}"
    print(f"Opening browser at {url} ...")
    webbrowser.open(url)

    try:
        # Keep parent alive until interrupted
        while process.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()


def print_usage():
    """Print usage information."""
    print("Usage: cp <command> [args...]")
    print("")
    print("Commands:")
    print("  server                        - Start HTTP server (API + built frontend)")
    print("  dev                           - Start server and open browser")
    print("  zectrix auth                  - Run Google OAuth (one-time)")
    print("  zectrix sync                  - Run a one-time calendar sync")
    print("  zectrix scheduler [--hours N] - Start the recurring sync (foreground)")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "server":
        run_server()
    elif cmd == "dev":
        run_dev()
    elif cmd == "zectrix":
        from cyber_persona.plugins.zectrix.cli import main as zectrix_main

        sys.argv = [sys.argv[0]] + sys.argv[2:]
        zectrix_main()
    else:
        print(f"Unknown command: {cmd}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
