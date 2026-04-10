"""Agno Toolkit wrapping the Erebus cron scheduler.

Gives the agent tools to create, list, update, enable/disable,
and delete scheduled tasks.  Cron expressions can be provided
directly or described in plain English (the agent translates them).
"""

from __future__ import annotations

import logging
from typing import Optional

from agno.tools.toolkit import Toolkit

from erebus.config import get_settings

logger = logging.getLogger(__name__)


class SchedulerTools(Toolkit):
    """Agent-facing tools for managing Erebus cron schedules."""

    def __init__(self) -> None:
        super().__init__(name="scheduler")
        self.register(self.list_schedules)
        self.register(self.create_schedule)
        self.register(self.delete_schedule)
        self.register(self.enable_schedule)
        self.register(self.disable_schedule)
        self.register(self.update_schedule)

    def list_schedules(self, enabled_only: bool = False) -> str:
        """List all cron schedules registered in Erebus.

        Parameters
        ----------
        enabled_only:
            If True, return only active (enabled) schedules.

        Returns
        -------
        str
            A formatted table of schedules with id, name, cron expression,
            status, and description.
        """
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(get_settings())
        entries = sched.list(enabled=True if enabled_only else None)

        if not entries:
            return "No schedules found."

        lines = [f"{'ID':<14}  {'Name':<20}  {'Cron':<15}  {'Status':<8}  Description"]
        lines.append("-" * 80)
        for e in entries:
            status = "enabled" if e.enabled else "disabled"
            lines.append(
                f"{e.id:<14}  {e.name:<20}  {e.cron:<15}  {status:<8}  {e.description}"
            )
        return "\n".join(lines)

    def create_schedule(
        self,
        name: str,
        cron: str,
        description: str = "",
        timezone: str = "UTC",
        notification_channel: Optional[str] = None,
    ) -> str:
        """Create a new cron schedule.

        Use standard 5-field cron syntax:  minute hour day month weekday
        Examples:
          - Every day at 8 AM      → "0 8 * * *"
          - Every Monday midnight  → "0 0 * * 1"
          - Every hour             → "0 * * * *"
          - Every 15 minutes       → "*/15 * * * *"

        Parameters
        ----------
        name:
            Short unique identifier for the schedule (e.g. "morning-report").
        cron:
            5-field cron expression.
        description:
            Human-readable description of what this schedule does.
        timezone:
            IANA timezone name (default "UTC").
        notification_channel:
            Optional name of a notification channel to alert when the
            schedule fires.

        Returns
        -------
        str
            Confirmation with the assigned schedule id, or an error message.
        """
        from erebus.scheduler.cron import ErebusScheduler

        try:
            sched = ErebusScheduler(get_settings())
            entry = sched.create(
                name=name,
                cron=cron,
                description=description,
                timezone=timezone,
                notification_channel=notification_channel,
            )
            return (
                f"Schedule created successfully.\n"
                f"  id:   {entry.id}\n"
                f"  name: {entry.name}\n"
                f"  cron: {entry.cron}\n"
                f"  tz:   {entry.timezone}\n"
                f"  desc: {entry.description}"
            )
        except ValueError as exc:
            return f"Failed to create schedule: {exc}"

    def delete_schedule(self, schedule_id: str) -> str:
        """Delete a cron schedule by its id.

        Parameters
        ----------
        schedule_id:
            The id returned by create_schedule or list_schedules.

        Returns
        -------
        str
            Confirmation or error message.
        """
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(get_settings())
        ok = sched.delete(schedule_id)
        if ok:
            return f"Schedule '{schedule_id}' deleted."
        return f"Schedule '{schedule_id}' not found."

    def enable_schedule(self, schedule_id: str) -> str:
        """Enable a previously disabled schedule.

        Parameters
        ----------
        schedule_id:
            The schedule id to enable.

        Returns
        -------
        str
            Confirmation or error message.
        """
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(get_settings())
        entry = sched.enable(schedule_id)
        if entry:
            return f"Schedule '{entry.name}' ({schedule_id}) enabled."
        return f"Schedule '{schedule_id}' not found."

    def disable_schedule(self, schedule_id: str) -> str:
        """Disable a schedule without deleting it.

        Parameters
        ----------
        schedule_id:
            The schedule id to disable.

        Returns
        -------
        str
            Confirmation or error message.
        """
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(get_settings())
        entry = sched.disable(schedule_id)
        if entry:
            return f"Schedule '{entry.name}' ({schedule_id}) disabled."
        return f"Schedule '{schedule_id}' not found."

    def update_schedule(
        self,
        schedule_id: str,
        name: Optional[str] = None,
        cron: Optional[str] = None,
        description: Optional[str] = None,
        timezone: Optional[str] = None,
        notification_channel: Optional[str] = None,
    ) -> str:
        """Update fields of an existing schedule.

        Only the provided (non-None) fields are changed.

        Parameters
        ----------
        schedule_id:
            Id of the schedule to update.
        name:
            New name (optional).
        cron:
            New 5-field cron expression (optional).
        description:
            New description (optional).
        timezone:
            New IANA timezone (optional).
        notification_channel:
            New notification channel name (optional).

        Returns
        -------
        str
            Updated schedule details or error message.
        """
        from erebus.scheduler.cron import ErebusScheduler

        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if cron is not None:
            kwargs["cron"] = cron
        if description is not None:
            kwargs["description"] = description
        if timezone is not None:
            kwargs["timezone"] = timezone
        if notification_channel is not None:
            kwargs["notification_channel"] = notification_channel

        if not kwargs:
            return "No fields to update provided."

        try:
            sched = ErebusScheduler(get_settings())
            entry = sched.update(schedule_id, **kwargs)
            if entry is None:
                return f"Schedule '{schedule_id}' not found."
            return (
                f"Schedule updated.\n"
                f"  id:   {entry.id}\n"
                f"  name: {entry.name}\n"
                f"  cron: {entry.cron}\n"
                f"  tz:   {entry.timezone}\n"
                f"  desc: {entry.description}\n"
                f"  enabled: {entry.enabled}"
            )
        except ValueError as exc:
            return f"Failed to update schedule: {exc}"
