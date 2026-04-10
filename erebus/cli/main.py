"""Erebus CLI — Rich-powered terminal interface.

Entry point: ``erebus`` (or ``python -m erebus.cli.main``).
Provides an interactive chat REPL, model switching, skill browsing,
schedule management, and a server launcher.
"""

from __future__ import annotations

import sys

from rich.prompt import Prompt

from erebus.cli.console import (
    console,
    print_error,
    print_info,
    print_panel,
    print_success,
    print_table,
    print_welcome,
    status_spinner,
)
from erebus.config import get_settings


def _handle_slash_command(command: str, agent, settings) -> bool:
    """Handle slash commands. Returns True if the command was recognized."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        print_info("Goodbye! 👋")
        return True  # signals exit

    if cmd == "/help":
        print_panel(
            "## Available Commands\n\n"
            "| Command | Description |\n"
            "|---------|-------------|\n"
            "| `/help` | Show this help |\n"
            "| `/model [provider:id]` | Show or switch model |\n"
            "| `/skills` | List registered skills |\n"
            "| `/memory [user_id]` | List memories |\n"
            "| `/schedules` | List cron schedules |\n"
            "| `/soul` | Show current personality |\n"
            "| `/context` | Show loaded AGENTS.md context |\n"
            "| `/new` | Start a new session |\n"
            "| `/quit` | Exit Erebus |\n",
            title="Help",
        )
        return False

    if cmd == "/model":
        if arg:
            settings.default_model = arg
            print_success(f"Model switched to: {arg}")
        else:
            print_info(f"Current model: {settings.default_model}")
        return False

    if cmd == "/skills":
        from erebus.skills.registry import list_skills

        skills = list_skills()
        if skills:
            rows = [
                [s.get("name", "?"), s.get("description", ""), s.get("source", "")]
                for s in skills
            ]
            print_table("Registered Skills", ["Name", "Description", "Source"], rows)
        else:
            print_info("No skills registered.")
        return False

    if cmd == "/context":
        from erebus.core.agent import _load_context_files

        ctx = _load_context_files()
        if ctx:
            print_panel(ctx, title="Project Context (AGENTS.md)")
        else:
            print_info("No AGENTS.md or CLAUDE.md context files found.")
        return False

    if cmd == "/memory":
        from erebus.memory.manager import ErebusMemory

        uid = arg or "default"
        mem = ErebusMemory(settings)
        memories = mem.list_memories(uid)
        if memories:
            rows = [
                [str(m.get("id", "")), str(m.get("content", "")), str(m.get("topics", ""))]
                for m in memories
            ]
            print_table(f"Memories for {uid}", ["ID", "Content", "Topics"], rows)
        else:
            print_info(f"No memories stored for user '{uid}'.")
        return False

    if cmd == "/schedules":
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(settings)
        entries = sched.list()
        if entries:
            rows = [
                [e.id, e.name, e.cron, "✓" if e.enabled else "✗", e.description]
                for e in entries
            ]
            print_table("Cron Schedules", ["ID", "Name", "Cron", "Enabled", "Description"], rows)
        else:
            print_info("No schedules configured.")
        return False

    if cmd == "/soul":
        from erebus.soul.loader import load_soul_instructions

        soul_text = load_soul_instructions(settings.soul_file)
        print_panel(soul_text, title="Soul / Personality")
        return False

    if cmd == "/new":
        import uuid

        new_sid = uuid.uuid4().hex[:12]
        print_success(f"New session started: {new_sid}")
        return False

    print_error(f"Unknown command: {cmd}. Type /help for available commands.")
    return False


def interactive_chat() -> None:
    """Run the interactive Rich-powered chat REPL."""
    settings = get_settings()
    print_welcome()
    print_info(f"Model: {settings.default_model}")

    # Show loaded context files (pi-mono style)
    from erebus.core.agent import _load_context_files

    context = _load_context_files()
    if context:
        print_info("AGENTS.md context loaded. Use /context to view.")

    print_info("Type /help for commands, /quit to exit.\n")

    from erebus.core.agent import create_agent

    agent = create_agent(settings=settings)
    session_id = "cli-session"

    while True:
        try:
            user_input = Prompt.ask("[bold bright_cyan]You[/bold bright_cyan]")
        except (KeyboardInterrupt, EOFError):
            print_info("\nGoodbye! 👋")
            break

        if not user_input.strip():
            continue

        if user_input.strip().startswith("/"):
            should_exit = _handle_slash_command(user_input.strip(), agent, settings)
            if should_exit:
                break
            continue

        with status_spinner("Thinking…"):
            try:
                response = agent.run(user_input, session_id=session_id, stream=False)
                content = response.content if hasattr(response, "content") else str(response)
            except Exception as exc:
                print_error(f"Agent error: {exc}")
                continue

        print_panel(content, title="Erebus", subtitle=settings.default_model)
        console.print()


def serve_gateway() -> None:
    """Start the unified Erebus gateway (API + channels + web UI)."""
    import uvicorn

    from erebus.gateway.server import create_gateway_app

    settings = get_settings()
    app = create_gateway_app(settings)
    print_info(f"Starting Erebus Gateway on {settings.api_host}:{settings.api_port}")
    print_info("  API:  /api/")
    if settings.telegram_token:
        print_info("  Telegram: /telegram/webhook")
    if settings.teams_app_id:
        print_info("  Teams: /api/messages")
    print_info("  Web UI: /")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


def serve_api() -> None:
    """Start the FastAPI REST API server."""
    import uvicorn

    from erebus.api.server import create_api_app

    settings = get_settings()
    app = create_api_app(settings)
    print_info(f"Starting Erebus API on {settings.api_host}:{settings.api_port}")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


def app() -> None:
    """Main CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] == "chat":
        interactive_chat()
    elif args[0] == "serve":
        serve_api()
    elif args[0] == "gateway":
        serve_gateway()
    elif args[0] == "telegram":
        _run_telegram()
    elif args[0] == "teams":
        _run_teams()
    elif args[0] == "version":
        from erebus import __version__

        print_info(f"Erebus v{__version__}")
    else:
        print_error(f"Unknown command: {args[0]}")
        print_info("Usage: erebus [chat|serve|gateway|telegram|teams|version]")
        sys.exit(1)


def _run_telegram() -> None:
    """Launch the Telegram bot."""
    import uvicorn

    from erebus.channels.telegram import create_telegram_app

    settings = get_settings()
    if not settings.telegram_token:
        print_error("EREBUS_TELEGRAM_TOKEN is not set.")
        sys.exit(1)
    app = create_telegram_app(settings)
    print_info("Starting Telegram bot…")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


def _run_teams() -> None:
    """Launch the Microsoft Teams bot."""
    import asyncio

    from aiohttp import web

    from erebus.channels.teams import TeamsBot

    settings = get_settings()
    if not settings.teams_app_id:
        print_error("EREBUS_TEAMS_APP_ID is not set.")
        sys.exit(1)

    async def _start() -> None:
        bot = TeamsBot(settings)
        web_app = await bot.create_app()
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, settings.api_host, settings.api_port)
        print_info(f"Teams bot listening on {settings.api_host}:{settings.api_port}")
        await site.start()
        await asyncio.Event().wait()

    asyncio.run(_start())


if __name__ == "__main__":
    app()
