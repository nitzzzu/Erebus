"""Skill registry — discovers and loads skill modules.

Skills are Python modules in the ``builtins`` sub-package or user-created
files under ``~/.erebus/skills/``.  Each module exposes a ``tools()``
function that returns a list of Agno ``Toolkit`` instances.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

from erebus.config import get_settings

# In-memory registry of skill metadata
_SKILL_META: list[dict[str, Any]] = []


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


def _discover_user_skills() -> list[dict[str, Any]]:
    """Discover user-created skill JSON descriptors in ~/.erebus/skills/."""
    settings = get_settings()
    skills_dir = settings.data_dir / "skills"
    skills: list[dict[str, Any]] = []
    if not skills_dir.exists():
        return skills
    for path in skills_dir.glob("*.json"):
        try:
            meta = json.loads(path.read_text())
            meta["source"] = "user"
            meta["path"] = str(path)
            skills.append(meta)
        except Exception:
            continue
    return skills


def refresh_registry() -> list[dict[str, Any]]:
    """Re-scan and return all skill metadata."""
    global _SKILL_META
    _SKILL_META = _discover_builtin_skills() + _discover_user_skills()
    return _SKILL_META


def list_skills() -> list[dict[str, Any]]:
    """Return the current skill registry, refreshing if empty."""
    if not _SKILL_META:
        refresh_registry()
    return list(_SKILL_META)


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
    """Persist a user-created skill to disk.

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
