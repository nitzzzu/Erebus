"""Notification channel manager backed by ~/.erebus/notifications.json.

Each entry in the JSON file represents an apprise-compatible URL with a
human-friendly name.  The manager provides CRUD operations and a helper to
fire notifications through any (or all) configured channels.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NotificationChannel:
    """A named apprise notification URL."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    url: str = ""
    enabled: bool = True
    is_default: bool = False


class NotificationManager:
    """File-backed manager for apprise notification channels.

    Channels are persisted as JSON in ``~/.erebus/notifications.json``.
    """

    def __init__(self, data_dir: Path) -> None:
        self._path: Path = data_dir / "notifications.json"
        self._channels: list[NotificationChannel] = self._load()

    # -- Persistence ----------------------------------------------------------

    def _load(self) -> list[NotificationChannel]:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                return [NotificationChannel(**entry) for entry in raw]
            except Exception:
                return []
        return []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([asdict(c) for c in self._channels], indent=2),
            encoding="utf-8",
        )

    # -- CRUD -----------------------------------------------------------------

    def list(self, *, enabled_only: bool = False) -> list[NotificationChannel]:
        if enabled_only:
            return [c for c in self._channels if c.enabled]
        return list(self._channels)

    def get(self, channel_id: str) -> Optional[NotificationChannel]:
        return next((c for c in self._channels if c.id == channel_id), None)

    def get_by_name(self, name: str) -> Optional[NotificationChannel]:
        return next((c for c in self._channels if c.name == name), None)

    def get_default(self) -> Optional[NotificationChannel]:
        """Return the default channel, falling back to the first enabled one."""
        default = next((c for c in self._channels if c.is_default and c.enabled), None)
        if default:
            return default
        enabled = [c for c in self._channels if c.enabled]
        return enabled[0] if enabled else None

    def _get_env_default(self) -> Optional["NotificationChannel"]:
        """Return a virtual channel built from EREBUS_APPRISE_DEFAULT_URL, if set."""
        try:
            from erebus.config import get_settings

            url = get_settings().apprise_default_url
        except Exception:
            url = None
        if not url:
            return None
        return NotificationChannel(
            id="env-default",
            name="env-default",
            url=url,
            enabled=True,
            is_default=True,
        )

    def create(
        self,
        name: str,
        url: str,
        enabled: bool = True,
        is_default: bool = False,
    ) -> NotificationChannel:
        if is_default:
            # Clear existing default
            for c in self._channels:
                c.is_default = False
        channel = NotificationChannel(name=name, url=url, enabled=enabled, is_default=is_default)
        self._channels.append(channel)
        self._save()
        return channel

    def update(self, channel_id: str, **kwargs) -> Optional[NotificationChannel]:
        channel = self.get(channel_id)
        if channel is None:
            return None
        if kwargs.get("is_default"):
            for c in self._channels:
                c.is_default = False
        for key, value in kwargs.items():
            if hasattr(channel, key):
                setattr(channel, key, value)
        self._save()
        return channel

    def delete(self, channel_id: str) -> bool:
        before = len(self._channels)
        self._channels = [c for c in self._channels if c.id != channel_id]
        if len(self._channels) < before:
            self._save()
            return True
        return False

    def set_default(self, channel_id: str) -> Optional[NotificationChannel]:
        return self.update(channel_id, is_default=True)

    # -- Notification ---------------------------------------------------------

    def send(
        self,
        message: str,
        title: str = "Erebus",
        channel_name: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> dict:
        """Send a notification via apprise.

        Resolves the target channel in this order:
        1. ``channel_id`` if provided
        2. ``channel_name`` if provided
        3. The default channel
        4. All enabled channels

        Returns a dict with ``{"sent": True/False, "channels": [...], "error": ...}``.
        """
        try:
            import apprise
        except ImportError:
            return {"sent": False, "channels": [], "error": "apprise not installed"}

        # Resolve channel(s)
        targets: list[NotificationChannel] = []
        if channel_id:
            ch = self.get(channel_id)
            if ch and ch.enabled:
                targets = [ch]
        elif channel_name:
            ch = self.get_by_name(channel_name)
            if ch and ch.enabled:
                targets = [ch]

        if not targets:
            default = self.get_default()
            if default:
                targets = [default]

        if not targets:
            # Fall back to EREBUS_APPRISE_DEFAULT_URL env var
            env_ch = self._get_env_default()
            if env_ch:
                targets = [env_ch]

        if not targets:
            # Broadcast to all enabled channels
            targets = [c for c in self._channels if c.enabled]

        if not targets:
            return {"sent": False, "channels": [], "error": "No notification channels configured"}

        ap = apprise.Apprise()
        channel_names: list[str] = []
        for ch in targets:
            try:
                ap.add(ch.url)
                channel_names.append(ch.name)
            except Exception as exc:
                logger.warning("Failed to add apprise URL for channel %s: %s", ch.name, exc)

        if not channel_names:
            return {"sent": False, "channels": [], "error": "All channel URLs are invalid"}

        try:
            ok = ap.notify(body=message, title=title)
            return {"sent": bool(ok), "channels": channel_names, "error": None}
        except Exception as exc:
            logger.exception("apprise notify error")
            return {"sent": False, "channels": channel_names, "error": str(exc)}
