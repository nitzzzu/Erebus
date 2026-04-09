"""Recursive skill loader — discovers SKILL.md files in nested directory trees.

Hermes-style skill organization:
    skills/
    ├── category/
    │   ├── DESCRIPTION.md          # Optional category description
    │   └── skill-name/
    │       ├── SKILL.md            # Required: instructions + YAML frontmatter
    │       ├── references/         # Optional: supporting docs
    │       └── scripts/            # Optional: executable helpers
    └── another-category/
        └── ...

This loader walks directories recursively, finds all SKILL.md files,
parses their frontmatter for metadata, and feeds them into Agno's
``Skills`` / ``LocalSkills`` machinery.  It also discovers
DESCRIPTION.md files to provide category-level metadata.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional

from agno.skills import LocalSkills, Skills

logger = logging.getLogger(__name__)

# Directories to skip during recursive scanning
EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".git", ".github", ".hub", "__pycache__", "node_modules", ".venv", "venv"}
)

# Platform name mapping (user-friendly → sys.platform values)
PLATFORM_MAP: dict[str, set[str]] = {
    "macos": {"darwin"},
    "mac": {"darwin"},
    "darwin": {"darwin"},
    "linux": {"linux"},
    "windows": {"win32", "cygwin"},
    "win": {"win32", "cygwin"},
}


def _parse_frontmatter(skill_md: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns a dict with keys: name, description, category, path, tags,
    platforms, metadata, and the raw frontmatter text.
    """
    result: dict[str, Any] = {
        "name": skill_md.parent.name,
        "description": "",
        "category": "",
        "path": str(skill_md),
        "tags": [],
        "platforms": [],
    }

    try:
        text = skill_md.read_text(encoding="utf-8")
    except Exception:
        return result

    if not text.startswith("---"):
        return result

    end = text.find("---", 3)
    if end == -1:
        return result

    frontmatter = text[3:end].strip()

    # Simple YAML-like parsing (avoids PyYAML dependency for frontmatter)
    for line in frontmatter.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            result["name"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            result["description"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("license:"):
            result["license"] = line.split(":", 1)[1].strip()
        elif line.startswith("platforms:"):
            # Parse inline list: [macos, linux]
            val = line.split(":", 1)[1].strip()
            if val.startswith("[") and val.endswith("]"):
                result["platforms"] = [
                    p.strip().strip('"').strip("'")
                    for p in val[1:-1].split(",")
                    if p.strip()
                ]

    return result


def _skill_matches_platform(frontmatter: dict[str, Any]) -> bool:
    """Check if a skill is compatible with the current OS platform."""
    platforms = frontmatter.get("platforms", [])
    if not platforms:
        return True  # No restriction → available everywhere

    current = sys.platform
    for p in platforms:
        p_lower = p.lower()
        if p_lower in PLATFORM_MAP:
            if current in PLATFORM_MAP[p_lower]:
                return True
        elif current.startswith(p_lower):
            return True
    return False


def _parse_category_description(desc_md: Path) -> str:
    """Read a DESCRIPTION.md and return its text content."""
    try:
        return desc_md.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def discover_skills(
    root_dir: Path,
    *,
    recursive: bool = True,
    filter_platform: bool = True,
) -> list[dict[str, Any]]:
    """Walk *root_dir* recursively and discover all SKILL.md-based skills.

    Parameters
    ----------
    root_dir:
        Top-level skills directory (e.g. ``erebus/skills/builtins``).
    recursive:
        If True (default), walk subdirectories at any depth.
    filter_platform:
        If True (default), skip skills whose ``platforms`` list excludes
        the current OS.

    Returns
    -------
    list[dict]
        List of skill metadata dicts with keys: name, description,
        category, path, tags, platforms, source.
    """
    skills: list[dict[str, Any]] = []
    if not root_dir.is_dir():
        return skills

    # Walk the tree looking for SKILL.md files
    pattern = root_dir.rglob("SKILL.md") if recursive else root_dir.glob("*/SKILL.md")
    for skill_md in sorted(pattern):
        # Skip excluded directories
        if any(part in EXCLUDED_DIRS for part in skill_md.parts):
            continue

        meta = _parse_frontmatter(skill_md)

        # Derive category from directory structure
        # e.g. builtins/software-development/tdd/SKILL.md → category="software-development"
        rel = skill_md.parent.relative_to(root_dir)
        parts = rel.parts
        if len(parts) >= 2:
            meta["category"] = parts[0]
        elif len(parts) == 1:
            # Skill directly under root
            meta["category"] = ""

        if filter_platform and not _skill_matches_platform(meta):
            logger.debug("Skipping skill %s (platform mismatch)", meta["name"])
            continue

        skills.append(meta)

    return skills


def discover_categories(root_dir: Path) -> list[dict[str, str]]:
    """Discover skill categories from DESCRIPTION.md files and directory names.

    Returns a list of dicts with keys: name, description.
    """
    categories: list[dict[str, str]] = []
    if not root_dir.is_dir():
        return categories

    for child in sorted(root_dir.iterdir()):
        if not child.is_dir() or child.name in EXCLUDED_DIRS:
            continue

        desc_md = child / "DESCRIPTION.md"
        description = _parse_category_description(desc_md) if desc_md.is_file() else ""

        # Only include if it has at least one SKILL.md somewhere inside
        has_skills = any(child.rglob("SKILL.md"))
        if has_skills:
            categories.append({"name": child.name, "description": description})

    return categories


def build_skills_from_dirs(
    *dirs: Path,
    extra_loaders: Optional[list[LocalSkills]] = None,
) -> Skills:
    """Build an Agno ``Skills`` object from one or more skill root directories.

    Each directory is registered as a ``LocalSkills`` loader.  Agno handles
    the actual SKILL.md parsing and tool registration; we just point it at
    the right directories.

    For hermes-style nested layouts (category/skill-name/SKILL.md), Agno's
    ``LocalSkills`` already walks subdirectories, so this works out of the box.

    Parameters
    ----------
    *dirs:
        One or more root directories containing SKILL.md-based skills.
    extra_loaders:
        Additional ``LocalSkills`` instances to merge in.
    """
    loaders: list[LocalSkills] = []

    for d in dirs:
        if d.is_dir():
            loaders.append(LocalSkills(str(d)))

    if extra_loaders:
        loaders.extend(extra_loaders)

    return Skills(loaders=loaders) if loaders else Skills(loaders=[])
