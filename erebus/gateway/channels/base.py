"""Abstract base class for messaging channels.

Inspired by nanobot's BaseChannel pattern: each channel inherits from
``BaseChannel`` and implements ``is_configured()`` to check credentials,
and ``mount()`` to attach routes onto the gateway FastAPI app.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from erebus.config import ErebusSettings

logger = logging.getLogger(__name__)


class BaseChannel(ABC):
    """Abstract messaging channel.

    Subclasses must implement:
    - ``name`` property — human-readable channel name.
    - ``is_configured()`` — whether required credentials are present.
    - ``mount()`` — attach routes/handlers onto the gateway FastAPI app.
    """

    def __init__(self, settings: "ErebusSettings") -> None:
        self._settings = settings

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable channel name (e.g. 'Telegram', 'Microsoft Teams')."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if all required configuration values are present."""

    @abstractmethod
    def mount(self, app: "FastAPI") -> None:
        """Mount channel endpoints onto the gateway FastAPI application."""

    def status(self) -> dict:
        """Return a status dict for the channels API."""
        configured = self.is_configured()
        return {
            "name": self.name,
            "configured": configured,
            "status": "active" if configured else "not_configured",
        }
