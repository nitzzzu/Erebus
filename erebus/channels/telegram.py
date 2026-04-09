"""Telegram channel integration using Agno's built-in Telegram interface.

Wraps Agno's ``agno.os.interfaces.telegram.Telegram`` to expose the
Erebus agent as a Telegram bot with webhook support.
"""

from __future__ import annotations

from typing import Optional

from erebus.config import ErebusSettings, get_settings
from erebus.core.agent import create_agent


def create_telegram_app(settings: Optional[ErebusSettings] = None):
    """Create and return a FastAPI application wired to a Telegram bot.

    Returns
    -------
    FastAPI
        A uvicorn-servable ASGI application.
    """
    from agno.os.app import AgentOS
    from agno.os.interfaces.telegram import Telegram

    if settings is None:
        settings = get_settings()

    agent = create_agent(settings=settings)

    telegram_interface = Telegram(agent=agent)

    agent_os = AgentOS(
        agents=[agent],
        interfaces=[telegram_interface],
    )

    return agent_os.get_app()
