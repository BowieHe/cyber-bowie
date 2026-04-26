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


def _warn_if_legacy(sync: CalendarSync) -> None:
    if sync.state.legacy_format_detected:
        print(
            "\n⚠️  检测到旧版同步状态(synced_event_ids 列表),无法迁移 todo_id 映射。"
            "\n   本次同步会重新创建所有 todos。"
            "\n   建议先在 Zectrix App 手动清空旧的同步条目,避免重复。\n"
        )


async def cmd_sync() -> None:
    sync = CalendarSync()
    _warn_if_legacy(sync)
    counts = await sync.run()
    print(
        f"\n✅ Sync complete. +{counts['created']} ~{counts['updated']} -{counts['deleted']}"
    )


def cmd_scheduler(args: argparse.Namespace) -> None:
    # Warn about legacy state format before starting the loop.
    _warn_if_legacy(CalendarSync())

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

    sub.add_parser("auth", help="Run Google OAuth authorization (one-time)")
    sub.add_parser("sync", help="Run a one-time manual sync")

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
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run sync immediately on start (default: True). Use --no-now to disable.",
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
