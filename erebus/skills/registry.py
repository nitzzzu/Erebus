"""Skill registry — discovers and loads skill modules and SKILL.md skills.

Skills are organized in a hermes-style nested directory tree:
    builtins/
    ├── category/
    │   ├── DESCRIPTION.md
    │   └── skill-name/
    │       └── SKILL.md

The registry supports:
  - Python module skills (``builtins`` sub-package)
  - SKILL.md-format skills in nested category/skill directories
  - User-created skill JSON descriptors in ``~/.erebus/skills/``
  - External skill directories via config

Uses ``erebus.skills.loader`` for recursive directory walking and
metadata extraction.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

from erebus.config import get_settings
from erebus.skills.loader import discover_categories, discover_skills

# In-memory registry of skill metadata
_SKILL_META: list[dict[str, Any]] = []

# Path to built-in skills directory
_BUILTINS_DIR = Path(__file__).parent / "builtins"


def _discover_builtin_skills() -> list[dict[str, Any]]:
    """Discover built-in skill modules under erebus.skills.builtins."""
    import erebus.skills.builtins as builtins_pkg

    skills: list[dict[str, Any]] = []
    for _importer, modname, _ispkg in pkgutil.iter_modules(builtins_pkg.__path__):
        mod = importlib.import_module(f"erebus.skills.builtins.{modname}")
        meta = getattr(mod, "SKILL_META", {"name": modname, "description": modname})
        meta["source"] = "builtin"
        meta["module"] = f"erebus.skills.builtins.{modname}"
        skills.append(meta)
    return skills


def _discover_builtin_skill_md() -> list[dict[str, Any]]:
    """Discover SKILL.md-format skills recursively in the builtins directory."""
    skills = discover_skills(_BUILTINS_DIR, recursive=True, filter_platform=True)
    for s in skills:
        s["source"] = "builtin-skill-md"
    return skills


def _discover_user_skills() -> list[dict[str, Any]]:
    """Discover user-created skills in ~/.erebus/skills/ and ~/.erebus/user-skills/."""
    settings = get_settings()
    skills: list[dict[str, Any]] = []

    # Legacy skills dir: JSON descriptors + SKILL.md files
    skills_dir = settings.data_dir / "skills"
    if skills_dir.exists():
        for path in sorted(skills_dir.glob("*.json")):
            try:
                meta = json.loads(path.read_text())
                meta["source"] = "user"
                meta["path"] = str(path)
                skills.append(meta)
            except Exception:
                continue

        md_skills = discover_skills(skills_dir, recursive=True, filter_platform=True)
        for s in md_skills:
            s["source"] = "user-skill-md"
        skills.extend(md_skills)

    # Agent-created skills dir: SKILL.md files created via the API / agent
    user_created_dir = settings.data_dir / "user-skills"
    if user_created_dir.exists():
        md_skills = discover_skills(user_created_dir, recursive=True, filter_platform=True)
        for s in md_skills:
            s["source"] = "user-created"
        skills.extend(md_skills)

    return skills


def _discover_external_skills() -> list[dict[str, Any]]:
    """Discover skills from external directories configured via config file."""
    from erebus.agent_config import get_config_section, load_agent_config

    config = load_agent_config()
    skills_config = get_config_section(config, "skills")
    extra_dirs = skills_config.get("extra_dirs", [])
    disabled = set(skills_config.get("disabled", []))

    skills: list[dict[str, Any]] = []
    for dir_path in extra_dirs:
        d = Path(dir_path).expanduser()
        if d.is_dir():
            found = discover_skills(d, recursive=True, filter_platform=True)
            for s in found:
                if s["name"] not in disabled:
                    s["source"] = "external"
                    skills.append(s)

    return skills


def _discover_github_skills() -> list[dict[str, Any]]:
    """Discover skills from GitHub-synced repositories."""
    try:
        from erebus.skills.github_loader import sync_all_github_skills

        github_dirs = sync_all_github_skills()
    except Exception:
        return []

    skills: list[dict[str, Any]] = []
    for d in github_dirs:
        if d.is_dir():
            found = discover_skills(d, recursive=True, filter_platform=True)
            for s in found:
                s["source"] = "github"
                skills.append(s)
    return skills


def refresh_registry() -> list[dict[str, Any]]:
    """Re-scan and return all skill metadata."""
    global _SKILL_META
    _SKILL_META = (
        _discover_builtin_skills()
        + _discover_builtin_skill_md()
        + _discover_user_skills()
        + _discover_external_skills()
        + _discover_github_skills()
    )
    return _SKILL_META


def list_skills() -> list[dict[str, Any]]:
    """Return the current skill registry, refreshing if empty."""
    if not _SKILL_META:
        refresh_registry()
    return list(_SKILL_META)


def list_skill_categories() -> list[dict[str, str]]:
    """Return the list of skill categories from the builtins directory."""
    categories = discover_categories(_BUILTINS_DIR)

    # Also check user skills directories
    settings = get_settings()
    for user_dir_name in ("skills", "user-skills"):
        user_dir = settings.data_dir / user_dir_name
        if user_dir.is_dir():
            user_cats = discover_categories(user_dir)
            existing_names = {c["name"] for c in categories}
            for c in user_cats:
                if c["name"] not in existing_names:
                    categories.append(c)

    return categories


def get_all_skill_tools():
    """Import and instantiate all Toolkit objects from registered skills."""
    from agno.tools.toolkit import Toolkit

    toolkits: list[Toolkit] = []
    for meta in list_skills():
        if meta.get("source") == "builtin" and meta.get("module"):
            try:
                mod = importlib.import_module(meta["module"])
                fn = getattr(mod, "tools", None)
                if callable(fn):
                    result = fn()
                    if isinstance(result, list):
                        toolkits.extend(result)
                    elif isinstance(result, Toolkit):
                        toolkits.append(result)
            except Exception:
                continue
    return toolkits


def save_user_skill(name: str, description: str, code: str) -> Path:
    """Persist a user-created skill to disk (legacy JSON format).

    Parameters
    ----------
    name:
        Short, unique skill name.
    description:
        Human-readable description.
    code:
        Python code that defines the skill.

    Returns
    -------
    Path
        Path to the saved skill JSON file.
    """
    settings = get_settings()
    skills_dir = settings.data_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skills_dir / f"{name}.json"
    skill_path.write_text(
        json.dumps(
            {"name": name, "description": description, "code": code},
            indent=2,
        )
    )
    refresh_registry()
    return skill_path


def save_user_skill_md(name: str, description: str, content: str, category: str = "") -> Path:
    """Persist a user-created skill as a SKILL.md file.

    Skills are stored in ``~/.erebus/user-skills/<category>/<name>/SKILL.md``
    (or ``~/.erebus/user-skills/<name>/SKILL.md`` when no category is given).
    This directory is separate from the built-in skills and is loaded by the
    agent at startup.

    Parameters
    ----------
    name:
        Short, unique skill name (used as the directory name).
    description:
        One-line description embedded in the SKILL.md frontmatter.
    content:
        Full SKILL.md body (instructions, usage guidelines, etc.).
    category:
        Optional category sub-directory.

    Returns
    -------
    Path
        Path to the saved SKILL.md file.
    """
    settings = get_settings()
    base_dir = settings.data_dir / "user-skills"
    if category:
        skill_dir = base_dir / category / name
    else:
        skill_dir = base_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    frontmatter = f"---\nname: {name}\ndescription: {description}\n---\n\n"
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(frontmatter + content, encoding="utf-8")
    refresh_registry()
    return skill_path
