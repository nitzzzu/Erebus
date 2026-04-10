"""Agno Toolkit wrapping apprise notification functionality.

Provides the agent with tools to send notifications and manage channels.
"""

from __future__ import annotations

import logging
from typing import Optional

from agno.tools.toolkit import Toolkit

from erebus.config import get_settings

logger = logging.getLogger(__name__)


class NotifyTools(Toolkit):
    """Agent-facing tools for sending notifications via apprise."""

    def __init__(self) -> None:
        super().__init__(name="notify")
        self.register(self.send_notification)
        self.register(self.list_notification_channels)

    def send_notification(
        self,
        message: str,
        title: str = "Erebus",
        channel: Optional[str] = None,
    ) -> str:
        """Send a notification to a configured notification channel.

        Parameters
        ----------
        message:
            The notification body text.
        title:
            Optional notification title (default: "Erebus").
        channel:
            Optional channel name to target. If omitted the default channel
            is used. If no default is set, the notification is broadcast to
            all enabled channels.

        Returns
        -------
        str
            A human-readable result string.
        """
        from erebus.notifications.manager import NotificationManager

        settings = get_settings()
        mgr = NotificationManager(settings.data_dir)
        result = mgr.send(message, title=title, channel_name=channel)

        if result["sent"]:
            ch_list = ", ".join(result["channels"])
            return f"Notification sent successfully via: {ch_list}"
        else:
            err = result.get("error") or "Unknown error"
            return f"Failed to send notification: {err}"

    def list_notification_channels(self) -> str:
        """List all configured notification channels.

        Returns
        -------
        str
            A formatted list of channels with their status.
        """
        from erebus.notifications.manager import NotificationManager

        settings = get_settings()
        mgr = NotificationManager(settings.data_dir)
        channels = mgr.list()

        if not channels:
            return "No notification channels configured."

        lines = ["Configured notification channels:"]
        for ch in channels:
            default_marker = " [default]" if ch.is_default else ""
            status = "enabled" if ch.enabled else "disabled"
            lines.append(f"  - {ch.name} ({status}){default_marker}")
        return "\n".join(lines)
