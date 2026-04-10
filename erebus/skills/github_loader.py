"""GitHub skill loader — clone or sync SKILL.md skills from GitHub repos.

Supports loading skills from public GitHub repositories and keeping them
in sync.  Skills are cached in ``~/.erebus/skills/github/<owner>/<repo>/``.

Configuration in ``erebus.toml``::

    [[skills.github]]
    repo = "owner/repo"
    path = "skills"           # subdirectory within the repo (default: root)
    ref = "main"              # branch/tag/commit (default: repo default branch)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from erebus.config import get_settings

logger = logging.getLogger(__name__)


def _github_skills_dir() -> Path:
    """Return the base directory for GitHub-synced skills."""
    settings = get_settings()
    d = settings.data_dir / "skills" / "github"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _repo_local_path(repo: str) -> Path:
    """Return the local cache path for a GitHub repo (owner/repo)."""
    parts = repo.strip("/").split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid repo format '{repo}' — expected 'owner/repo'")
    return _github_skills_dir() / parts[0] / parts[1]


def sync_github_repo(
    repo: str,
    path: str = "",
    ref: str = "",
) -> Path:
    """Clone or pull a GitHub repository to the local skills cache.

    Parameters
    ----------
    repo:
        GitHub repository in ``owner/repo`` format.
    path:
        Subdirectory within the repo containing skills (default: root).
    ref:
        Branch, tag, or commit to checkout (default: repo default).

    Returns
    -------
    Path
        The local directory containing the synced skills.
    """
    local_path = _repo_local_path(repo)
    url = f"https://github.com/{repo}.git"

    if local_path.is_dir() and (local_path / ".git").is_dir():
        # Already cloned — pull latest
        logger.info("Syncing GitHub skills repo: %s", repo)
        try:
            cmd = ["git", "-C", str(local_path), "pull", "--ff-only"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
            if result.returncode != 0:
                logger.warning(
                    "Failed to sync %s: %s", repo, result.stderr.strip() or result.stdout.strip()
                )
        except Exception:
            logger.warning("Failed to sync %s — using cached version", repo)
    else:
        # Fresh clone
        logger.info("Cloning GitHub skills repo: %s", repo)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", "--depth", "1", url, str(local_path)]
        if ref:
            cmd = ["git", "clone", "--depth", "1", "--branch", ref, url, str(local_path)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
        except subprocess.CalledProcessError as exc:
            logger.error("Failed to clone %s: %s", repo, exc.stderr)
            raise RuntimeError(f"Failed to clone {repo}") from exc

    # If a specific ref was requested post-clone, checkout
    if ref and local_path.is_dir():
        try:
            subprocess.run(
                ["git", "-C", str(local_path), "checkout", ref],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except Exception:
            pass  # Best-effort checkout

    # Return the skills subdirectory
    skills_path = local_path / path if path else local_path
    return skills_path


def sync_all_github_skills(config: dict[str, Any] | None = None) -> list[Path]:
    """Sync all GitHub skills repos from configuration.

    Parameters
    ----------
    config:
        The skills section from erebus.toml. If None, loads from config.

    Returns
    -------
    list[Path]
        Directories containing synced skills.
    """
    if config is None:
        from erebus.agent_config import get_config_section, load_agent_config

        agent_config = load_agent_config()
        config = get_config_section(agent_config, "skills")

    github_repos = config.get("github", [])
    if not github_repos:
        return []

    paths: list[Path] = []
    for entry in github_repos:
        if isinstance(entry, str):
            # Simple format: "owner/repo"
            repo = entry
            path = ""
            ref = ""
        elif isinstance(entry, dict):
            repo = entry.get("repo", "")
            path = entry.get("path", "")
            ref = entry.get("ref", "")
        else:
            continue

        if not repo:
            continue

        try:
            skills_path = sync_github_repo(repo, path=path, ref=ref)
            if skills_path.is_dir():
                paths.append(skills_path)
                logger.info("GitHub skills available at: %s", skills_path)
        except Exception:
            logger.exception("Failed to sync GitHub skills from %s", repo)

    return paths


def remove_github_skills(repo: str) -> bool:
    """Remove a cached GitHub skills repo.

    Parameters
    ----------
    repo:
        GitHub repository in ``owner/repo`` format.

    Returns
    -------
    bool
        True if the repo was removed, False if not found.
    """
    local_path = _repo_local_path(repo)
    if local_path.is_dir():
        shutil.rmtree(local_path)
        return True
    return False
