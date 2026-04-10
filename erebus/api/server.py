"""FastAPI REST API server for Erebus web UI.

Exposes endpoints for chat (sync + SSE streaming), sessions, memory,
skills, schedules, soul, channels, and settings management.
"""

from __future__ import annotations

import asyncio
import json
import logging
import traceback
import uuid
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from erebus.api.sessions import (
    Session,
    all_sessions,
    delete_session,
    load_session,
    new_session,
    rename_session,
    save_session,
)
from erebus.config import ErebusSettings, get_settings

logger = logging.getLogger(__name__)


def asdict_session(session: Session) -> dict:
    """Convert session dataclass to dict (avoids inline import)."""
    from dataclasses import asdict

    return asdict(session)

# ── Request / Response Models ────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web-session"
    user_id: str = "web-user"
    model: Optional[str] = None


class ChatResponse(BaseModel):
    content: str
    session_id: str
    model: str


class ChatStreamRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "web-user"
    model: Optional[str] = None


class SessionCreateRequest(BaseModel):
    title: str = "New Chat"
    model: Optional[str] = None


class SessionRenameRequest(BaseModel):
    title: str


class SkillCreateMdRequest(BaseModel):
    name: str
    description: str
    content: str
    category: str = ""


class SkillCreateLegacyRequest(BaseModel):
    name: str
    description: str
    code: str


class ScheduleCreateRequest(BaseModel):
    name: str
    cron: str
    description: str = ""
    payload: dict[str, Any] = {}
    timezone: str = "UTC"
    notification_channel: Optional[str] = None


class ScheduleUpdateRequest(BaseModel):
    name: Optional[str] = None
    cron: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    payload: Optional[dict[str, Any]] = None
    timezone: Optional[str] = None
    notification_channel: Optional[str] = None


class SoulRequest(BaseModel):
    content: str


class SettingsResponse(BaseModel):
    default_model: str
    reasoning_model: Optional[str] = None
    skills_dir: Optional[str] = None
    telegram_configured: bool = False
    teams_configured: bool = False
    apprise_default_url_configured: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8741


class NotificationChannelModel(BaseModel):
    id: str
    name: str
    url: str
    enabled: bool = True
    is_default: bool = False


class NotificationChannelCreateRequest(BaseModel):
    name: str
    url: str
    enabled: bool = True
    is_default: bool = False


class NotificationChannelUpdateRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class NotificationTestRequest(BaseModel):
    message: str = "Test notification from Erebus"
    title: str = "Erebus Test"
    channel_id: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    default_model: Optional[str] = None
    reasoning_model: Optional[str] = None
    skills_dir: Optional[str] = None


# ── Streaming Helpers ────────────────────────────────────────────────────────

# Active streams: stream_id -> asyncio.Queue
_streams: dict[str, asyncio.Queue] = {}

# Truncation limits
_MAX_TITLE_LEN = 60
_MAX_TOOL_ARGS_LEN = 200
_MAX_TOOL_RESULT_LEN = 500


def _generate_title(message: str) -> str:
    """Generate a short session title from the first user message."""
    title = message.strip().replace("\n", " ")
    if len(title) > _MAX_TITLE_LEN:
        title = title[: _MAX_TITLE_LEN - 3] + "..."
    return title


# ── App Factory ──────────────────────────────────────────────────────────────


def create_api_app(settings: Optional[ErebusSettings] = None) -> FastAPI:
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Erebus API",
        version="0.1.0",
        description="REST API for the Erebus AI agent",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Chat (sync, backward compatible) ------------------------------------

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(req: ChatRequest):
        from erebus.core.agent import create_agent

        model = req.model or settings.default_model
        agent = create_agent(settings=settings)
        try:
            response = agent.run(
                req.message,
                session_id=req.session_id,
                user_id=req.user_id,
                stream=False,
            )
            content = response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        return ChatResponse(content=content, session_id=req.session_id, model=model)

    # -- Chat SSE Streaming --------------------------------------------------

    @app.post("/api/chat/start")
    async def chat_start(req: ChatStreamRequest):
        """Start a streaming chat and return a stream_id for SSE connection."""
        model = req.model or settings.default_model

        # Resolve or create session
        if req.session_id:
            session = load_session(settings.data_dir, req.session_id)
            if session is None:
                session = new_session(settings.data_dir, model, title="New Chat")
        else:
            session = new_session(settings.data_dir, model, title=_generate_title(req.message))

        # Append user message to session
        session.messages.append({"role": "user", "content": req.message})
        save_session(settings.data_dir, session)

        stream_id = uuid.uuid4().hex[:16]
        queue: asyncio.Queue = asyncio.Queue()
        _streams[stream_id] = queue

        # Run agent in background thread
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            _run_agent_streaming,
            settings,
            session,
            req.message,
            model,
            req.user_id,
            stream_id,
            queue,
            loop,
        )

        return {
            "stream_id": stream_id,
            "session_id": session.session_id,
        }

    @app.get("/api/chat/stream")
    async def chat_stream(request: Request, stream_id: str):
        """SSE endpoint — connect with the stream_id from /api/chat/start."""
        if stream_id not in _streams:
            raise HTTPException(status_code=404, detail="Stream not found")

        queue = _streams[stream_id]

        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30)
                    except asyncio.TimeoutError:
                        yield {"event": "heartbeat", "data": ""}
                        continue

                    event_type = event.get("event", "message")
                    data = json.dumps(event.get("data", {}))
                    yield {"event": event_type, "data": data}

                    if event_type in ("done", "error"):
                        break
            finally:
                _streams.pop(stream_id, None)

        return EventSourceResponse(event_generator(), ping=15)

    # -- Ask User Answer -----------------------------------------------------

    class AnswerRequest(BaseModel):
        answer: str

    @app.post("/api/chat/answer/{stream_id}")
    async def chat_answer(stream_id: str, req: AnswerRequest):
        """Deliver a user answer to a waiting ask_user tool call."""
        from erebus.tools.ask_user import deliver_answer

        ok = deliver_answer(stream_id, req.answer)
        if not ok:
            raise HTTPException(
                status_code=404,
                detail=f"No active ask_user waiting for stream '{stream_id}'",
            )
        return {"delivered": True, "stream_id": stream_id}

    # -- Sessions ------------------------------------------------------------

    @app.get("/api/sessions")
    async def list_sessions():
        return {"sessions": all_sessions(settings.data_dir)}

    @app.post("/api/sessions")
    async def create_session(req: SessionCreateRequest):
        model = req.model or settings.default_model
        session = new_session(settings.data_dir, model, title=req.title)
        return session.compact()

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        session = load_session(settings.data_dir, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session": asdict_session(session)}

    @app.put("/api/sessions/{session_id}/rename")
    async def rename_session_endpoint(session_id: str, req: SessionRenameRequest):
        session = rename_session(settings.data_dir, session_id, req.title)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.compact()

    @app.delete("/api/sessions/{session_id}")
    async def delete_session_endpoint(session_id: str):
        ok = delete_session(settings.data_dir, session_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"deleted": True}

    # -- Memory --------------------------------------------------------------

    @app.get("/api/memory/{user_id}")
    async def list_memories(user_id: str):
        from erebus.memory.manager import ErebusMemory

        mem = ErebusMemory(settings)
        return {"memories": mem.list_memories(user_id)}

    @app.delete("/api/memory/{memory_id}")
    async def delete_memory(memory_id: str):
        from erebus.memory.manager import ErebusMemory

        mem = ErebusMemory(settings)
        ok = mem.delete_memory(memory_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"deleted": True}

    # -- Skills --------------------------------------------------------------

    @app.get("/api/skills")
    async def list_skills():
        from erebus.skills.registry import list_skills as _ls

        return {"skills": _ls()}

    @app.get("/api/skills/categories")
    async def list_skill_categories():
        from erebus.skills.registry import list_skill_categories

        return {"categories": list_skill_categories()}

    @app.get("/api/skills/category/{category}")
    async def list_skills_by_category(category: str):
        from erebus.skills.registry import list_skills as _ls

        skills = [s for s in _ls() if s.get("category") == category]
        return {"category": category, "skills": skills}

    @app.post("/api/skills")
    async def create_skill(req: SkillCreateMdRequest):
        from erebus.skills.registry import save_user_skill_md

        path = save_user_skill_md(req.name, req.description, req.content, req.category)
        return {"saved": True, "path": str(path)}

    @app.post("/api/skills/legacy")
    async def create_skill_legacy(req: SkillCreateLegacyRequest):
        from erebus.skills.registry import save_user_skill

        path = save_user_skill(req.name, req.description, req.code)
        return {"saved": True, "path": str(path)}

    # -- MCP Servers ---------------------------------------------------------

    @app.get("/api/mcp/servers")
    async def list_mcp_servers():
        from erebus.agent_config import get_config_section, load_agent_config
        from erebus.mcp import parse_mcp_configs

        config = load_agent_config()
        mcp_section = get_config_section(config, "mcp")
        configs = parse_mcp_configs(mcp_section)
        return {
            "servers": [
                {
                    "name": c.name,
                    "transport": c.transport,
                    "command": c.command,
                    "url": c.url,
                    "enabled": c.enabled,
                }
                for c in configs
            ]
        }

    # -- Agent Config --------------------------------------------------------

    @app.get("/api/config")
    async def get_agent_config():
        from erebus.agent_config import load_agent_config

        config = load_agent_config()
        return {"config": config}

    # -- Schedules -----------------------------------------------------------

    @app.get("/api/schedules")
    async def list_schedules():
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(settings)
        return {"schedules": [s.__dict__ for s in sched.list()]}

    @app.post("/api/schedules")
    async def create_schedule(req: ScheduleCreateRequest):
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(settings)
        try:
            entry = sched.create(
                name=req.name,
                cron=req.cron,
                description=req.description,
                payload=req.payload,
                timezone=req.timezone,
                notification_channel=req.notification_channel,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return entry.__dict__

    @app.put("/api/schedules/{schedule_id}")
    async def update_schedule(schedule_id: str, req: ScheduleUpdateRequest):
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(settings)
        updates = req.model_dump(exclude_none=True)
        entry = sched.update(schedule_id, **updates)
        if entry is None:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return entry.__dict__

    @app.delete("/api/schedules/{schedule_id}")
    async def delete_schedule(schedule_id: str):
        from erebus.scheduler.cron import ErebusScheduler

        sched = ErebusScheduler(settings)
        ok = sched.delete(schedule_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"deleted": True}

    # -- Soul / Personality --------------------------------------------------

    @app.get("/api/soul")
    async def get_soul():
        from erebus.soul.loader import load_soul_instructions

        return {"content": load_soul_instructions(settings.soul_file)}

    @app.put("/api/soul")
    async def update_soul(req: SoulRequest):
        from erebus.soul.loader import save_soul

        path = save_soul(req.content)
        return {"saved": True, "path": str(path)}

    # -- Context Files (AGENTS.md) -------------------------------------------

    @app.get("/api/context")
    async def get_context():
        from erebus.core.agent import _load_context_files

        return {"content": _load_context_files()}

    # -- Channels ------------------------------------------------------------

    @app.get("/api/channels")
    async def list_channels():
        channels = []
        channels.append(
            {
                "name": "Telegram",
                "configured": bool(settings.telegram_token),
                "status": "active" if settings.telegram_token else "not_configured",
            }
        )
        channels.append(
            {
                "name": "Microsoft Teams",
                "configured": bool(settings.teams_app_id),
                "status": "active" if settings.teams_app_id else "not_configured",
            }
        )
        channels.append(
            {
                "name": "Web UI",
                "configured": True,
                "status": "active",
            }
        )
        return {"channels": channels}

    # -- Settings ------------------------------------------------------------

    @app.get("/api/settings", response_model=SettingsResponse)
    async def get_settings_endpoint():
        return SettingsResponse(
            default_model=settings.default_model,
            reasoning_model=settings.reasoning_model,
            skills_dir=settings.skills_dir,
            telegram_configured=bool(settings.telegram_token),
            teams_configured=bool(settings.teams_app_id),
            apprise_default_url_configured=bool(settings.apprise_default_url),
            api_host=settings.api_host,
            api_port=settings.api_port,
        )

    @app.put("/api/settings")
    async def update_settings_endpoint(req: SettingsUpdateRequest):
        if req.default_model:
            settings.default_model = req.default_model
        if req.reasoning_model is not None:
            settings.reasoning_model = req.reasoning_model
        if req.skills_dir is not None:
            settings.skills_dir = req.skills_dir
        return {"updated": True}

    # -- Notification Channels -----------------------------------------------

    @app.get("/api/notifications/channels")
    async def list_notification_channels():
        from erebus.notifications.manager import NotificationManager

        mgr = NotificationManager(settings.data_dir)
        channels = mgr.list()
        return {"channels": [vars(c) for c in channels]}

    @app.post("/api/notifications/channels", response_model=NotificationChannelModel)
    async def create_notification_channel(req: NotificationChannelCreateRequest):
        from erebus.notifications.manager import NotificationManager

        mgr = NotificationManager(settings.data_dir)
        ch = mgr.create(
            name=req.name,
            url=req.url,
            enabled=req.enabled,
            is_default=req.is_default,
        )
        return NotificationChannelModel(**vars(ch))

    @app.put("/api/notifications/channels/{channel_id}", response_model=NotificationChannelModel)
    async def update_notification_channel(
        channel_id: str, req: NotificationChannelUpdateRequest
    ):
        from erebus.notifications.manager import NotificationManager

        mgr = NotificationManager(settings.data_dir)
        updates = req.model_dump(exclude_none=True)
        ch = mgr.update(channel_id, **updates)
        if ch is None:
            raise HTTPException(status_code=404, detail="Channel not found")
        return NotificationChannelModel(**vars(ch))

    @app.delete("/api/notifications/channels/{channel_id}")
    async def delete_notification_channel(channel_id: str):
        from erebus.notifications.manager import NotificationManager

        mgr = NotificationManager(settings.data_dir)
        ok = mgr.delete(channel_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Channel not found")
        return {"deleted": True}

    @app.post("/api/notifications/test")
    async def test_notification(req: NotificationTestRequest):
        from erebus.notifications.manager import NotificationManager

        mgr = NotificationManager(settings.data_dir)
        result = mgr.send(
            message=req.message,
            title=req.title,
            channel_id=req.channel_id,
        )
        if not result["sent"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Send failed"))
        return {"sent": result["sent"], "channels": result["channels"]}

    # -- Health --------------------------------------------------------------

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # -- Workspaces ----------------------------------------------------------

    class WorkspaceCreateRequest(BaseModel):
        name: str
        path: str
        description: str = ""

    class WorkspaceUpdateRequest(BaseModel):
        path: Optional[str] = None
        description: Optional[str] = None

    class WorkspaceSetSessionRequest(BaseModel):
        session_id: str

    @app.get("/api/workspaces")
    async def list_workspaces():
        """List all configured workspaces."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        return {"workspaces": [w.as_dict() for w in mgr.list()]}

    @app.post("/api/workspaces")
    async def create_workspace(req: WorkspaceCreateRequest):
        """Create a new workspace."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        try:
            resolved = mgr._safe_path(req.path)
            if not resolved.exists():
                raise HTTPException(status_code=400, detail=f"Path does not exist: {resolved}")
            ws = mgr.create(req.name, str(resolved), req.description)
            return ws.as_dict()
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    @app.get("/api/workspaces/{name}")
    async def get_workspace(name: str):
        """Get a workspace by name."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        ws = mgr.get(name)
        if ws is None:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found")
        return ws.as_dict()

    @app.put("/api/workspaces/{name}")
    async def update_workspace(name: str, req: WorkspaceUpdateRequest):
        """Update workspace path or description."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        ws = mgr.update(name, path=req.path, description=req.description)
        if ws is None:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found")
        return ws.as_dict()

    @app.delete("/api/workspaces/{name}")
    async def delete_workspace(name: str):
        """Delete a workspace."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        ok = mgr.delete(name)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found")
        return {"deleted": True}

    @app.post("/api/workspaces/{name}/activate")
    async def activate_workspace(name: str, req: WorkspaceSetSessionRequest):
        """Associate a workspace with a chat session."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        ws = mgr.get(name)
        if ws is None:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found")
        mgr.set_session_workspace(req.session_id, name)
        return {"activated": True, "workspace": ws.as_dict(), "session_id": req.session_id}

    @app.get("/api/sessions/{session_id}/workspace")
    async def get_session_workspace(session_id: str):
        """Get the workspace currently associated with a session."""
        from erebus.workspace.manager import WorkspaceManager

        mgr = WorkspaceManager(settings.data_dir)
        ws = mgr.get_session_workspace(session_id)
        if ws is None:
            return {"workspace": None}
        return {"workspace": ws.as_dict()}

    return app


# ── Agent Streaming Runner ───────────────────────────────────────────────────


def _run_agent_streaming(
    settings: ErebusSettings,
    session: Session,
    message: str,
    model: str,
    user_id: str,
    stream_id: str,
    queue: asyncio.Queue,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """Run the agent in a background thread, pushing SSE events into the queue."""
    from agno.agent import RunEvent

    from erebus.core.agent import create_agent
    from erebus.tools.ask_user import register_stream, unregister_stream

    def _put(event_type: str, data: Any) -> None:
        asyncio.run_coroutine_threadsafe(
            queue.put({"event": event_type, "data": data}),
            loop,
        )

    # Register SSE stream for AskUserTools
    register_stream(stream_id, _put)
    try:
        # Resolve workspace for this session
        workspace_path: Optional[str] = None
        try:
            from erebus.workspace.manager import WorkspaceManager
            ws_mgr = WorkspaceManager(settings.data_dir)
            ws = ws_mgr.get_session_workspace(session.session_id)
            if ws:
                workspace_path = ws.path
        except Exception:
            pass

        agent = create_agent(
            settings=settings,
            user_id=user_id,
            session_id=session.session_id,
            workspace_path=workspace_path,
            stream_id=stream_id,
        )
        full_content = ""

        response_iter = agent.run(
            message,
            session_id=session.session_id,
            user_id=user_id,
            stream=True,
            stream_events=True,
        )

        for chunk in response_iter:
            if chunk.event == RunEvent.tool_call_started:
                tool_info = {
                    "name": chunk.tool.tool_name if chunk.tool else "unknown",
                    "args": str(chunk.tool.tool_args)[:_MAX_TOOL_ARGS_LEN] if chunk.tool else "",
                }
                _put("tool_start", tool_info)

            elif chunk.event == RunEvent.tool_call_completed:
                result_str = ""
                if chunk.tool and chunk.tool.result is not None:
                    result_str = str(chunk.tool.result)[:_MAX_TOOL_RESULT_LEN]
                tool_info = {
                    "name": chunk.tool.tool_name if chunk.tool else "unknown",
                    "result": result_str,
                }
                _put("tool_end", tool_info)

            elif chunk.event == RunEvent.run_content:
                text = chunk.content or ""
                if text:
                    full_content += text
                    _put("token", {"text": text})

            elif chunk.event == RunEvent.run_started:
                _put("run_started", {})

            elif chunk.event == RunEvent.run_completed:
                pass  # Handled below in done

        # Save assistant message to session
        session.messages.append({"role": "assistant", "content": full_content})

        # Auto-title: if this is the first exchange, set session title
        if len(session.messages) == 2:
            session.title = _generate_title(session.messages[0].get("content", "New Chat"))

        save_session(settings.data_dir, session)

        _put("done", {
            "session_id": session.session_id,
            "model": model,
            "title": session.title,
        })

    except Exception as exc:
        logger.exception("Agent streaming error")
        _put("error", {
            "message": str(exc),
            "trace": traceback.format_exc()[-500:],
        })
    finally:
        unregister_stream(stream_id)
