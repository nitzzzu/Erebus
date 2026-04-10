"""Telegram channel — uses Agno's built-in Telegram interface.

Mounts the Telegram webhook endpoint under ``/telegram/`` on the
gateway's FastAPI app so that the Telegram bot runs in the same
process as the API and web UI.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from erebus.gateway.channels.base import BaseChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

    from erebus.config import ErebusSettings

logger = logging.getLogger(__name__)


class TelegramChannel(BaseChannel):
    """Telegram bot channel backed by Agno's Telegram interface."""

    def __init__(self, settings: "ErebusSettings") -> None:
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "Telegram"

    def is_configured(self) -> bool:
        return bool(self._settings.telegram_token)

    def mount(self, app: "FastAPI") -> None:
        """Mount Telegram webhook routes onto the gateway app."""
        if not self.is_configured():
            logger.info("Telegram channel not configured — skipping mount")
            return

        from agno.os.interfaces.telegram import Telegram

        from erebus.core.agent import create_agent

        agent = create_agent(settings=self._settings)
        telegram_interface = Telegram(agent=agent)
        router = telegram_interface.get_router()
        app.include_router(router)
        logger.info("Telegram channel mounted at /telegram/")
