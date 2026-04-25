"""Zectrix plugin: sync Google Calendar to Zectrix e-ink device as todos."""

from cyber_persona.plugins.zectrix.scheduler.jobs import start_scheduler, stop_scheduler

__all__ = ["start_scheduler", "stop_scheduler"]
