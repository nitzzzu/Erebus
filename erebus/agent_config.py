"""Agent configuration loader — reads TOML or JSON config files.

Supports loading from:
  1. ``erebus.toml`` in the current working directory
  2. ``erebus.json`` in the current working directory
  3. ``~/.erebus/erebus.toml``
  4. ``~/.erebus/erebus.json``
  5. Path specified by ``EREBUS_CONFIG`` environment variable

Precedence: env var > cwd > home dir.  TOML is preferred over JSON
when both exist at the same path.

Example erebus.toml:

    [agent]
    name = "Erebus"
    default_model = "openai:gpt-4o"
    reasoning_model = "anthropic:claude-sonnet-4-20250514"
    instructions = "You are a helpful assistant."

    [skills]
    extra_dirs = ["~/my-skills", "/shared/skills"]
    disabled = ["red-teaming"]

    [[mcp.servers]]
    name = "filesystem"
    command = "npx"
    args = ["-y", "@modelcontextprotocol/server-filesystem", "/home"]

    [[mcp.servers]]
    name = "brave-search"
    url = "https://mcp.brave.com/sse"
    transport = "sse"
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Python 3.11+ has tomllib in the stdlib
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover — Python < 3.11
    tomllib = None  # type: ignore[assignment]


def _load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file and return its contents as a dict."""
    if tomllib is None:
        raise ImportError("Python 3.11+ is required for TOML support (tomllib)")
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file and return its contents as a dict."""
    return json.loads(path.read_text(encoding="utf-8"))


def _find_config_file() -> Path | None:
    """Search for the configuration file in standard locations.

    Returns the first file found, or None.
    """
    # 1. Environment variable override
    env_path = os.environ.get("EREBUS_CONFIG")
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_file():
            return p
        logger.warning("EREBUS_CONFIG=%s not found", env_path)

    # 2. Current working directory
    cwd = Path.cwd()
    for name in ("erebus.toml", "erebus.json"):
        candidate = cwd / name
        if candidate.is_file():
            return candidate

    # 3. Home data directory (~/.erebus/)
    home_dir = Path(os.environ.get("EREBUS_DATA_DIR", str(Path.home() / ".erebus")))
    for name in ("erebus.toml", "erebus.json"):
        candidate = home_dir / name
        if candidate.is_file():
            return candidate

    return None


def load_agent_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load agent configuration from a TOML or JSON file.

    Parameters
    ----------
    path:
        Explicit path to a config file.  If ``None``, searches
        the standard locations.

    Returns
    -------
    dict
        The parsed configuration.  Empty dict if no config file found.
    """
    if path is not None:
        config_path = Path(path).expanduser()
    else:
        config_path = _find_config_file()

    if config_path is None:
        logger.debug("No agent config file found")
        return {}

    logger.info("Loading agent config from %s", config_path)

    try:
        if config_path.suffix == ".toml":
            return _load_toml(config_path)
        elif config_path.suffix == ".json":
            return _load_json(config_path)
        else:
            # Try TOML first, then JSON
            try:
                return _load_toml(config_path)
            except Exception:
                return _load_json(config_path)
    except Exception:
        logger.exception("Failed to load config from %s", config_path)
        return {}


def get_config_section(config: dict[str, Any], section: str) -> dict[str, Any]:
    """Get a section from the config dict, returning empty dict if missing."""
    return config.get(section, {})
