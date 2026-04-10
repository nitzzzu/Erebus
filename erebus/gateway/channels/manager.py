"""Channel manager — discovers and activates enabled channels.

Inspired by nanobot's ChannelManager: config-driven enable/disable,
centralized channel lifecycle, and status monitoring.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from erebus.gateway.channels.base import BaseChannel
from erebus.gateway.channels.teams_channel import TeamsChannel
from erebus.gateway.channels.telegram_channel import TelegramChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

    from erebus.config import ErebusSettings

logger = logging.getLogger(__name__)

# Registry of built-in channel classes
_CHANNEL_CLASSES: list[type[BaseChannel]] = [
    TelegramChannel,
    TeamsChannel,
]


class ChannelManager:
    """Manages all messaging channels for the gateway.

    Creates channel instances, mounts configured ones onto the
    FastAPI app, and provides status information.
    """

    def __init__(self, settings: "ErebusSettings") -> None:
        self._settings = settings
        self._channels: list[BaseChannel] = [cls(settings) for cls in _CHANNEL_CLASSES]

    def mount_all(self, app: "FastAPI") -> None:
        """Mount all configured channels onto the gateway app."""
        for channel in self._channels:
            if channel.is_configured():
                try:
                    channel.mount(app)
                    logger.info("Channel '%s' mounted successfully", channel.name)
                except (ImportError, RuntimeError, ValueError, OSError) as exc:
                    logger.error("Failed to mount channel '%s': %s", channel.name, exc)
            else:
                logger.debug("Channel '%s' not configured — skipped", channel.name)

    def status_all(self) -> list[dict]:
        """Return status for all channels (configured or not)."""
        statuses = [ch.status() for ch in self._channels]
        # Always include Web UI as active
        statuses.append({
            "name": "Web UI",
            "configured": True,
            "status": "active",
        })
        return statuses
