"""Core Erebus agent built on Agno framework.

Combines multi-model support, agentic memory, persistent storage,
skills, cron scheduling, MCP integration, and soul/personality
in a single agent factory.

Pi-mono style capabilities are enabled by default:
- FileTools: read, write, edit, search files
- ShellTools: execute shell/bash commands
- Agno Skills: SKILL.md-based on-demand domain expertise (hermes-style categories)
- MCP: Model Context Protocol server integration
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.skills import Skills
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.shell import ShellTools

from erebus.agent_config import get_config_section, load_agent_config
from erebus.config import ErebusSettings, get_settings
from erebus.skills.loader import build_skills_from_dirs
from erebus.skills.registry import get_all_skill_tools
from erebus.soul.loader import load_soul_instructions
from erebus.tools.notify import NotifyTools

if TYPE_CHECKING:
    from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

# Path to the built-in SKILL.md skills bundled with erebus
_BUILTIN_SKILLS_DIR = Path(__file__).parent.parent / "skills" / "builtins"

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _build_model(model_str: str, settings: "ErebusSettings"):
    """Parse ``provider:model_id`` and return the appropriate Agno model object.

    Supported providers:
    - ``openai``        — OpenAI or any custom OpenAI-compatible endpoint
    - ``azure_foundry`` — Azure AI Foundry
    - ``openrouter``    — OpenRouter (OpenAI-compatible)
    - ``claude`` / ``anthropic`` — Anthropic Claude
    """
    if ":" in model_str:
        provider, model_id = model_str.split(":", 1)
    else:
        provider, model_id = "openai", model_str

    provider = provider.lower()

    if provider in ("azure_foundry", "azure"):
        from agno.models.azure import AzureAIFoundry

        kwargs: dict = {
            "id": model_id,
            "api_key": settings.azure_foundry_api_key,
            "azure_endpoint": settings.azure_foundry_endpoint,
        }
        if settings.azure_foundry_api_version:
            kwargs["api_version"] = settings.azure_foundry_api_version
        return AzureAIFoundry(**kwargs)

    if provider == "openrouter":
        from agno.models.openai import OpenAIChat

        return OpenAIChat(
            id=model_id,
            api_key=settings.openrouter_api_key,
            base_url=_OPENROUTER_BASE_URL,
        )

    if provider in ("claude", "anthropic"):
        from agno.models.anthropic import Claude

        kwargs = {"id": model_id}
        if settings.anthropic_api_key:
            kwargs["api_key"] = settings.anthropic_api_key
        if settings.anthropic_endpoint:
            kwargs["client_params"] = {"base_url": settings.anthropic_endpoint}
        return Claude(**kwargs)

    # Default: openai (with optional custom endpoint)
    from agno.models.openai import OpenAIChat

    kwargs = {"id": model_id}
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    if settings.openai_endpoint:
        kwargs["base_url"] = settings.openai_endpoint
    return OpenAIChat(**kwargs)


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


def _build_skills(settings: ErebusSettings) -> "Skills":
    """Build the Agno Skills object from built-in, user, and external skill directories."""
    skill_dirs: list[Path] = []

    # Built-in SKILL.md skills (hermes-style categories)
    if _BUILTIN_SKILLS_DIR.exists():
        skill_dirs.append(_BUILTIN_SKILLS_DIR)

    # User-configured skills directory (env / .env)
    if settings.skills_dir:
        skills_path = Path(settings.skills_dir)
        if skills_path.exists():
            skill_dirs.append(skills_path)

    # ~/.erebus/skills/ as SKILL.md-style directory (legacy/external)
    user_skills_dir = settings.data_dir / "skills"
    if user_skills_dir.exists():
        skill_dirs.append(user_skills_dir)

    # ~/.erebus/user-skills/ — skills created by the agent or via the API
    agent_created_skills_dir = settings.data_dir / "user-skills"
    if agent_created_skills_dir.exists():
        skill_dirs.append(agent_created_skills_dir)

    # External skills directories from agent config file
    agent_config = load_agent_config()
    skills_config = get_config_section(agent_config, "skills")
    for extra_dir in skills_config.get("extra_dirs", []):
        p = Path(extra_dir).expanduser()
        if p.is_dir():
            skill_dirs.append(p)

    # GitHub-synced skills
    try:
        from erebus.skills.github_loader import sync_all_github_skills

        github_dirs = sync_all_github_skills(skills_config)
        skill_dirs.extend(github_dirs)
    except Exception:
        logger.debug("GitHub skills sync skipped (git not available or config missing)")

    return build_skills_from_dirs(*skill_dirs)


def create_agent(
    settings: Optional[ErebusSettings] = None,
    extra_tools: Optional[list["Toolkit"]] = None,
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
        A ready-to-use Agno agent with comprehensive capabilities.
    """
    if settings is None:
        settings = get_settings()

    # Load agent config file (TOML/JSON)
    agent_config = load_agent_config()
    agent_section = get_config_section(agent_config, "agent")

    db = SqliteDb(db_file=settings.db_path)

    # Core tools: web search + file operations + shell (pi-mono style) + notifications
    tools: list[Toolkit] = [
        DuckDuckGoTools(),
        FileTools(),
        ShellTools(),
        NotifyTools(),
    ]

    # Legacy Python-module skills (backward compatibility)
    tools.extend(get_all_skill_tools())

    if extra_tools:
        tools.extend(extra_tools)

    # Agno Skills — SKILL.md format (hermes-style nested categories)
    skills = _build_skills(settings)

    # Soul / personality instructions + AGENTS.md context files
    soul_instructions = load_soul_instructions(settings.soul_file)
    context_files = _load_context_files()

    # Build instructions from soul + config + context
    instructions = soul_instructions

    # Override from config file if present
    config_instructions = agent_section.get("instructions")
    if config_instructions:
        instructions = f"{instructions}\n\n{config_instructions}"

    if context_files:
        instructions = f"{instructions}\n\n## Project Context\n\n{context_files}"

    # Model override from config
    model_str = agent_section.get("default_model", settings.default_model)
    reasoning_model_str = agent_section.get("reasoning_model", settings.reasoning_model)

    model = _build_model(model_str, settings)
    reasoning_model = _build_model(reasoning_model_str, settings) if reasoning_model_str else None

    # Memory manager — reuses the same model object (already constructed above)
    memory_manager = MemoryManager(model=model, db=db)

    agent_kwargs: dict = {
        "name": agent_section.get("name", "Erebus"),
        "model": model,
        "tools": tools,
        "skills": skills,
        "db": db,
        "memory_manager": memory_manager,
        "enable_agentic_memory": settings.enable_agentic_memory,
        "learning": settings.enable_learning,
        "add_history_to_context": True,
        "num_history_runs": 10,
        "add_datetime_to_context": True,
        "markdown": True,
        "instructions": instructions,
    }

    if reasoning_model:
        agent_kwargs["reasoning_model"] = reasoning_model

    agent = Agent(**agent_kwargs)

    return agent
