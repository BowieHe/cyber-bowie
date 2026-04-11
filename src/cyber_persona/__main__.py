"""Entry point."""
import subprocess
import sys
import time


def run_server():
    """Run the SSE server."""
    import uvicorn
    from cyber_persona.server.ws_server import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


def run_tui():
    """Run the TUI client."""
    from cyber_persona.client.tui import main
    main()


def run_dev():
    """Run both server and TUI."""
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


def main():
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: cp [server|tui|dev]")
        print("")
        print("Commands:")
        print("  server  - Start WebSocket server only")
        print("  tui     - Start TUI client only (server must be running)")
        print("  dev     - Start both server and TUI")
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
        print("Usage: cp [server|tui|dev]")
        sys.exit(1)


if __name__ == "__main__":
    main()
