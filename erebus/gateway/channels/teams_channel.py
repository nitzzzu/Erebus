"""Microsoft Teams channel — uses Bot Framework SDK.

Mounts the Teams ``/api/messages`` endpoint onto the gateway's FastAPI
app so that the Teams bot runs in the same process.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from erebus.gateway.channels.base import BaseChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

    from erebus.config import ErebusSettings

logger = logging.getLogger(__name__)


class TeamsChannel(BaseChannel):
    """Microsoft Teams bot channel."""

    def __init__(self, settings: "ErebusSettings") -> None:
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "Microsoft Teams"

    def is_configured(self) -> bool:
        return bool(self._settings.teams_app_id)

    def mount(self, app: "FastAPI") -> None:
        """Mount Teams message endpoint onto the gateway app."""
        if not self.is_configured():
            logger.info("Teams channel not configured — skipping mount")
            return

        from botbuilder.core import (
            BotFrameworkAdapter,
            BotFrameworkAdapterSettings,
            TurnContext,
        )
        from fastapi import Request, Response

        from erebus.core.agent import create_agent

        adapter_settings = BotFrameworkAdapterSettings(
            app_id=self._settings.teams_app_id or "",
            app_password=self._settings.teams_app_password or "",
        )
        adapter = BotFrameworkAdapter(adapter_settings)
        agent = create_agent(settings=self._settings)

        @app.post("/api/messages")
        async def teams_messages(request: Request):
            """Handle incoming Teams bot messages."""
            if request.headers.get("content-type") != "application/json":
                return Response(status_code=415)
            body = await request.json()

            from botbuilder.schema import Activity

            activity = Activity().deserialize(body)
            auth_header = request.headers.get("Authorization", "")

            async def on_message(turn_context: TurnContext) -> None:
                user_text = turn_context.activity.text or ""
                user_id = (
                    turn_context.activity.from_property.id
                    if turn_context.activity.from_property
                    else "teams-user"
                )
                response = agent.run(user_text, user_id=user_id)
                content = response.content if hasattr(response, "content") else str(response)
                await turn_context.send_activity(content)

            await adapter.process_activity(activity, auth_header, on_message)
            return Response(status_code=200)

        logger.info("Teams channel mounted at /api/messages")
