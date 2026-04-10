"""Telegram channel — uses Agno's built-in Telegram interface.

Mounts the Telegram webhook endpoint under ``/telegram/`` on the
gateway's FastAPI app so that the Telegram bot runs in the same
process as the API and web UI.

User filtering is implemented via a lightweight ASGI middleware that
reads the incoming Telegram update, checks the sender's ID against
``EREBUS_TELEGRAM_ALLOWED_USERS``, and rejects unknown senders before
Agno ever sees the request.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from erebus.gateway.channels.base import BaseChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

    from erebus.config import ErebusSettings

logger = logging.getLogger(__name__)


def _parse_allowed_users(raw: str | None) -> frozenset[str]:
    """Parse a comma-separated list of Telegram user IDs into a frozenset."""
    if not raw:
        return frozenset()
    return frozenset(uid.strip() for uid in raw.split(",") if uid.strip())


class _TelegramUserFilter:
    """ASGI middleware that rejects Telegram webhook calls from unknown users."""

    def __init__(self, app, allowed: frozenset[str], webhook_path: str = "/telegram/webhook") -> None:
        self._app = app
        self._allowed = allowed
        self._webhook_path = webhook_path

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http" or scope.get("path") != self._webhook_path:
            await self._app(scope, receive, send)
            return

        # Buffer the full request body so we can inspect it and replay it.
        body_chunks: list[bytes] = []
        more_body = True
        while more_body:
            msg = await receive()
            body_chunks.append(msg.get("body", b""))
            more_body = msg.get("more_body", False)
        body = b"".join(body_chunks)

        try:
            data = json.loads(body)
            update = data.get("message") or data.get("edited_message") or {}
            user_id = str(update.get("from", {}).get("id", ""))
            if user_id and user_id not in self._allowed:
                logger.debug("Telegram: rejected update from user %s (not in allowed list)", user_id)
                response_body = json.dumps({"status": "ignored"}).encode()
                await send({"type": "http.response.start", "status": 200,
                            "headers": [(b"content-type", b"application/json"),
                                        (b"content-length", str(len(response_body)).encode())]})
                await send({"type": "http.response.body", "body": response_body})
                return
        except Exception:
            pass  # malformed body — let Agno handle it

        # Replay the buffered body for downstream handlers.
        replayed = False

        async def replay_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        await self._app(scope, replay_receive, send)


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
        telegram_interface = Telegram(
            agent=agent,
            token=self._settings.telegram_token,
        )
        router = telegram_interface.get_router()
        app.include_router(router)

        # Apply user allowlist filtering if configured.
        allowed = _parse_allowed_users(self._settings.telegram_allowed_users)
        if allowed:
            logger.info(
                "Telegram channel: restricting access to %d user(s): %s",
                len(allowed),
                ", ".join(sorted(allowed)),
            )
            app.middleware_stack = None  # force rebuild after adding middleware
            app.add_middleware(_TelegramUserFilter, allowed=allowed)

        logger.info("Telegram channel mounted at /telegram/")
