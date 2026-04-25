"""CLI entry point for the Zectrix plugin.

Commands:
    auth        Run Google OAuth flow (one-time)
    sync        Run a one-time manual sync
    scheduler   Start the background scheduler

Usage:
    python -m cyber_persona.plugins.zectrix.cli auth
    python -m cyber_persona.plugins.zectrix.cli sync
    python -m cyber_persona.plugins.zectrix.cli scheduler [--hours 12]
"""

import argparse
import asyncio
import logging
import sys

from cyber_persona.plugins.zectrix.calendar_sync.auth import run_auth_flow
from cyber_persona.plugins.zectrix.calendar_sync.sync import CalendarSync
from cyber_persona.plugins.zectrix.scheduler.jobs import start_scheduler


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def cmd_sync() -> None:
    sync = CalendarSync()
    count = await sync.run()
    print(f"\n✅ Sync complete. Created {count} new todos.")


def cmd_scheduler(args: argparse.Namespace) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    scheduler = start_scheduler(
        hours=args.hours,
        minutes=args.minutes,
        run_immediately=args.now,
    )

    print(
        f"\n🕐 Scheduler running. Sync every {args.hours}h {args.minutes}m."
    )
    print("   Press Ctrl+C to stop.\n")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopping scheduler...")
        scheduler.shutdown()


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        prog="zectrix",
        description="Zectrix plugin: sync Google Calendar to your e-ink device",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # auth
    sub.add_parser("auth", help="Run Google OAuth authorization (one-time)")

    # sync
    sub.add_parser("sync", help="Run a one-time manual sync")

    # scheduler
    sched_parser = sub.add_parser("scheduler", help="Start background scheduler")
    sched_parser.add_argument(
        "--hours",
        type=int,
        default=12,
        help="Sync interval in hours (default: 12)",
    )
    sched_parser.add_argument(
        "--minutes",
        type=int,
        default=0,
        help="Additional minutes (default: 0)",
    )
    sched_parser.add_argument(
        "--now",
        action="store_true",
        default=True,
        help="Run sync immediately on start (default: True)",
    )

    args = parser.parse_args()

    if args.command == "auth":
        run_auth_flow()
    elif args.command == "sync":
        asyncio.run(cmd_sync())
    elif args.command == "scheduler":
        cmd_scheduler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
