"""Load and manage soul/personality definitions.

A *soul* is a markdown file (like Hermes' SOUL.md) that shapes the agent's
personality, tone, and behavioral constraints.  It is injected as the
agent's ``instructions``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from erebus.config import get_settings

DEFAULT_SOUL = """\
You are **Erebus**, a highly capable AI assistant.

## Core Traits
- Friendly, concise, and insightful.
- Always cite sources when providing factual information.
- Proactively use tools and skills when they can help.
- Remember user preferences across conversations.

## Communication Style
- Use markdown formatting for clarity.
- When presenting lists or data, prefer tables.
- Keep responses focused — quality over quantity.
"""


def load_soul_instructions(path: Optional[str] = None) -> str:
    """Load personality instructions from a SOUL.md file.

    Falls back to the built-in default soul if no file is provided or found.
    """
    if path:
        p = Path(path)
        if p.is_file():
            return p.read_text(encoding="utf-8")

    # Try default location
    settings = get_settings()
    default_path = settings.data_dir / "SOUL.md"
    if default_path.is_file():
        return default_path.read_text(encoding="utf-8")

    return DEFAULT_SOUL


def save_soul(content: str, path: Optional[str] = None) -> Path:
    """Save soul content to disk."""
    settings = get_settings()
    target = Path(path) if path else settings.data_dir / "SOUL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def get_default_soul() -> str:
    """Return the built-in default soul text."""
    return DEFAULT_SOUL
