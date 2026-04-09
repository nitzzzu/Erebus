"""FastAPI REST API server for Erebus web UI.

Exposes endpoints for chat, memory, skills, schedules, soul,
channels, and settings management.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from erebus.config import ErebusSettings, get_settings

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


class SkillCreateRequest(BaseModel):
    name: str
    description: str
    code: str


class ScheduleCreateRequest(BaseModel):
    name: str
    cron: str
    description: str = ""
    payload: dict[str, Any] = {}
    timezone: str = "UTC"


class ScheduleUpdateRequest(BaseModel):
    name: Optional[str] = None
    cron: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    payload: Optional[dict[str, Any]] = None
    timezone: Optional[str] = None


class SoulRequest(BaseModel):
    content: str


class SettingsResponse(BaseModel):
    default_model: str
    reasoning_model: Optional[str] = None
    skills_dir: Optional[str] = None
    telegram_configured: bool = False
    teams_configured: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8741


class SettingsUpdateRequest(BaseModel):
    default_model: Optional[str] = None
    reasoning_model: Optional[str] = None
    skills_dir: Optional[str] = None


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

    # -- Chat ----------------------------------------------------------------

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

    @app.post("/api/skills")
    async def create_skill(req: SkillCreateRequest):
        from erebus.skills.registry import save_user_skill

        path = save_user_skill(req.name, req.description, req.code)
        return {"saved": True, "path": str(path)}

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

    # -- Health --------------------------------------------------------------

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app
