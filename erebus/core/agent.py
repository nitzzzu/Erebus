"""Core Erebus agent built on Agno framework.

Combines multi-model support, agentic memory, persistent storage,
skills, cron scheduling, and soul/personality in a single agent factory.

Pi-mono style capabilities are enabled by default:
- FileTools: read, write, edit, search files
- ShellTools: execute shell/bash commands
- Agno Skills: SKILL.md-based on-demand domain expertise
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.skills import LocalSkills, Skills
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.shell import ShellTools

from erebus.config import ErebusSettings, get_settings
from erebus.skills.registry import get_all_skill_tools
from erebus.soul.loader import load_soul_instructions

if TYPE_CHECKING:
    from agno.tools.toolkit import Toolkit

# Path to the built-in SKILL.md skills bundled with erebus
_BUILTIN_SKILLS_DIR = Path(__file__).parent.parent / "skills" / "builtins"


def _load_context_files() -> str:
    """Load AGENTS.md / CLAUDE.md context files (pi-mono style).

    Reads from ~/.erebus/AGENTS.md and the current working directory,
    returning their combined contents as additional instructions.
    """
    settings = get_settings()
    parts: list[str] = []

    # Global context file
    for name in ("AGENTS.md", "CLAUDE.md"):
        global_path = settings.data_dir / name
        if global_path.is_file():
            parts.append(global_path.read_text(encoding="utf-8"))
            break

    # Project-level context file (cwd)
    cwd = Path(os.getcwd())
    for name in ("AGENTS.md", "CLAUDE.md"):
        local_path = cwd / name
        if local_path.is_file():
            parts.append(local_path.read_text(encoding="utf-8"))
            break

    return "\n\n".join(parts)


def _build_skills(settings: ErebusSettings) -> Skills:
    """Build the Agno Skills object from built-in and user skill directories."""
    loaders: list[LocalSkills] = []

    # Built-in SKILL.md skills
    if _BUILTIN_SKILLS_DIR.exists():
        loaders.append(LocalSkills(str(_BUILTIN_SKILLS_DIR)))

    # User-configured skills directory
    if settings.skills_dir:
        skills_path = Path(settings.skills_dir)
        if skills_path.exists():
            loaders.append(LocalSkills(str(skills_path)))

    # ~/.erebus/skills/ as SKILL.md-style directory
    user_skills_dir = settings.data_dir / "skills"
    if user_skills_dir.exists():
        loaders.append(LocalSkills(str(user_skills_dir)))

    return Skills(loaders=loaders) if loaders else Skills(loaders=[])


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
        A ready-to-use Agno agent with pi-mono coding capabilities.
    """
    if settings is None:
        settings = get_settings()

    db = SqliteDb(db_file=settings.db_path)

    # Memory manager — uses the same (or cheaper) model for memory extraction
    memory_manager = MemoryManager(
        model=settings.default_model,
        db=db,
    )

    # Core tools: web search + file operations + shell (pi-mono style)
    tools: list[Toolkit] = [
        DuckDuckGoTools(),
        FileTools(),
        ShellTools(),
    ]

    # Legacy Python-module skills (backward compatibility)
    tools.extend(get_all_skill_tools())

    if extra_tools:
        tools.extend(extra_tools)

    # Agno Skills — SKILL.md format (official Anthropic Agent Skills spec)
    skills = _build_skills(settings)

    # Soul / personality instructions + AGENTS.md context files
    soul_instructions = load_soul_instructions(settings.soul_file)
    context_files = _load_context_files()
    instructions = soul_instructions
    if context_files:
        instructions = f"{soul_instructions}\n\n## Project Context\n\n{context_files}"

    agent_kwargs: dict = {
        "name": "Erebus",
        "model": settings.default_model,
        "tools": tools,
        "skills": skills,
        "db": db,
        "memory_manager": memory_manager,
        "enable_agentic_memory": True,
        "add_history_to_context": True,
        "num_history_runs": 10,
        "add_datetime_to_context": True,
        "markdown": True,
        "instructions": instructions,
    }

    if settings.reasoning_model:
        agent_kwargs["reasoning_model"] = settings.reasoning_model

    agent = Agent(**agent_kwargs)

    return agent
