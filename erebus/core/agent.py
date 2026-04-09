"""Core Erebus agent built on Agno framework.

Combines multi-model support, agentic memory, persistent storage,
skills, cron scheduling, and soul/personality in a single agent factory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.tools.duckduckgo import DuckDuckGoTools

from erebus.config import ErebusSettings, get_settings
from erebus.skills.registry import get_all_skill_tools
from erebus.soul.loader import load_soul_instructions

if TYPE_CHECKING:
    from agno.tools.toolkit import Toolkit


def create_agent(
    settings: Optional[ErebusSettings] = None,
    extra_tools: Optional[list[Toolkit]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Agent:
    """Create and return a fully-configured Erebus agent.

    Parameters
    ----------
    settings:
        Erebus settings (loaded from env if not provided).
    extra_tools:
        Additional tool instances to attach.
    session_id:
        Optional session identifier for storage continuity.
    user_id:
        Optional user identifier for memory scoping.

    Returns
    -------
    Agent
        A ready-to-use Agno agent.
    """
    if settings is None:
        settings = get_settings()

    db = SqliteDb(db_file=settings.db_path)

    # Memory manager — uses the same (or cheaper) model for memory extraction
    memory_manager = MemoryManager(
        model=settings.default_model,
        db=db,
    )

    # Collect tools: built-in search + registered skills + extras
    tools: list[Toolkit] = [DuckDuckGoTools()]
    tools.extend(get_all_skill_tools())
    if extra_tools:
        tools.extend(extra_tools)

    # Soul / personality instructions
    soul_instructions = load_soul_instructions(settings.soul_file)

    agent_kwargs: dict = {
        "name": "Erebus",
        "model": settings.default_model,
        "tools": tools,
        "db": db,
        "memory_manager": memory_manager,
        "enable_agentic_memory": True,
        "add_history_to_context": True,
        "num_history_runs": 10,
        "add_datetime_to_context": True,
        "markdown": True,
        "instructions": soul_instructions,
    }

    if settings.reasoning_model:
        agent_kwargs["reasoning_model"] = settings.reasoning_model

    agent = Agent(**agent_kwargs)

    return agent
