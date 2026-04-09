"""Microsoft Teams bot channel.

Uses the Bot Framework SDK (``botbuilder-core``) to expose the Erebus
agent as a Teams bot.  The bot receives messages via an ``/api/messages``
endpoint and streams agent responses back to the conversation.
"""

from __future__ import annotations

from typing import Optional

from erebus.config import ErebusSettings, get_settings


class TeamsBot:
    """Minimal Microsoft Teams bot backed by Erebus agent."""

    def __init__(self, settings: Optional[ErebusSettings] = None) -> None:
        if settings is None:
            settings = get_settings()
        self._settings = settings

    async def create_app(self):
        """Build an aiohttp web application for the Teams bot.

        Returns
        -------
        aiohttp.web.Application
            An aiohttp app ready to serve ``/api/messages``.
        """
        from aiohttp import web
        from botbuilder.core import (
            BotFrameworkAdapter,
            BotFrameworkAdapterSettings,
            TurnContext,
        )

        from erebus.core.agent import create_agent

        adapter_settings = BotFrameworkAdapterSettings(
            app_id=self._settings.teams_app_id or "",
            app_password=self._settings.teams_app_password or "",
        )
        adapter = BotFrameworkAdapter(adapter_settings)

        agent = create_agent(settings=self._settings)

        async def on_message(turn_context: TurnContext) -> None:
            user_text = turn_context.activity.text or ""
            user_id = (
                turn_context.activity.from_property.id
                if turn_context.activity.from_property
                else "teams-user"
            )
            response = agent.run(user_text, user_id=user_id)
            await turn_context.send_activity(response.content)

        async def messages_handler(request: web.Request) -> web.Response:
            if request.content_type != "application/json":
                return web.Response(status=415)
            body = await request.json()

            from botbuilder.schema import Activity

            activity = Activity().deserialize(body)
            auth_header = request.headers.get("Authorization", "")
            await adapter.process_activity(activity, auth_header, on_message)
            return web.Response(status=200)

        app = web.Application()
        app.router.add_post("/api/messages", messages_handler)
        return app
