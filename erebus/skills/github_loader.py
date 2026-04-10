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
                err = result.stderr.strip() or result.stdout.strip() or "unknown error"
                logger.warning("Failed to sync %s: %s", repo, err)
        except (subprocess.SubprocessError, OSError):
            logger.warning("Failed to sync %s — using cached version", repo)
    else:
        # Fresh clone
        logger.info("Cloning GitHub skills repo: %s", repo)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", "--depth", "1"]
        if ref:
            cmd.extend(["--branch", ref])
        cmd.extend([url, str(local_path)])
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
        except (subprocess.SubprocessError, OSError):
            logger.debug("Failed to checkout ref '%s' for %s", ref, repo)

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
        except (RuntimeError, ValueError, OSError):
            logger.exception("Failed to sync GitHub skills from %s", repo)

    return paths


def install_skill_from_github_url(url: str) -> Path:
    """Install a skill from a GitHub folder URL using sparse checkout.

    Accepts URLs in these formats:
      - ``https://github.com/owner/repo/tree/branch/path/to/skill``
      - ``https://github.com/owner/repo`` (root of repo)

    The skill folder is copied into ``~/.erebus/user-skills/`` so the
    agent picks it up on the next registry refresh.

    Parameters
    ----------
    url:
        GitHub URL pointing to a skill folder.

    Returns
    -------
    Path
        The installed skill directory under ``~/.erebus/user-skills/``.

    Raises
    ------
    ValueError
        If the URL cannot be parsed as a GitHub folder URL.
    RuntimeError
        If the sparse checkout or copy operation fails.
    """
    import re
    import tempfile

    # Parse the GitHub URL
    # https://github.com/{owner}/{repo}/tree/{ref}/{path}
    pattern = re.compile(
        r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+)(?:/(.+))?)?/?$"
    )
    m = pattern.match(url.rstrip("/"))
    if not m:
        raise ValueError(
            f"Cannot parse GitHub URL: {url!r}. "
            "Expected format: https://github.com/owner/repo/tree/branch/path/to/skill"
        )

    owner, repo_name, ref, subpath = m.group(1), m.group(2), m.group(3), m.group(4)
    repo_slug = f"{owner}/{repo_name}"
    ref = ref or ""
    subpath = subpath.strip("/") if subpath else ""

    # Determine skill name from the last component of subpath (or repo name)
    skill_name = Path(subpath).name if subpath else repo_name

    settings = get_settings()
    user_skills_dir = settings.data_dir / "user-skills"
    user_skills_dir.mkdir(parents=True, exist_ok=True)
    dest = user_skills_dir / skill_name

    # Use a temp directory for the sparse clone
    with tempfile.TemporaryDirectory(prefix="erebus-skill-") as tmpdir:
        clone_dir = Path(tmpdir) / "repo"
        clone_url = f"https://github.com/{repo_slug}.git"

        # Initialise an empty repo and configure sparse-checkout
        init_cmds: list[list[str]] = [
            ["git", "init", str(clone_dir)],
            ["git", "-C", str(clone_dir), "remote", "add", "origin", clone_url],
            ["git", "-C", str(clone_dir), "config", "core.sparseCheckout", "true"],
        ]
        for cmd in init_cmds:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
            if result.returncode != 0:
                raise RuntimeError(
                    f"git command failed: {' '.join(cmd)}\n{result.stderr}"
                )

        # Write the sparse-checkout pattern
        sparse_file = clone_dir / ".git" / "info" / "sparse-checkout"
        sparse_file.parent.mkdir(parents=True, exist_ok=True)
        pattern_str = f"{subpath}/*\n" if subpath else "/*\n"
        sparse_file.write_text(pattern_str)

        # Pull the desired ref (or default branch)
        fetch_cmd = ["git", "-C", str(clone_dir), "pull", "--depth", "1", "origin"]
        if ref:
            fetch_cmd.append(ref)
        else:
            fetch_cmd.append("HEAD")

        result = subprocess.run(fetch_cmd, capture_output=True, text=True, timeout=120, check=False)
        if result.returncode != 0:
            # Try without specifying HEAD (let git pick the default branch)
            fetch_cmd2 = ["git", "-C", str(clone_dir), "pull", "--depth", "1", "origin"]
            result2 = subprocess.run(
                fetch_cmd2, capture_output=True, text=True, timeout=120, check=False
            )
            if result2.returncode != 0:
                raise RuntimeError(
                    f"Failed to fetch {repo_slug}: {result.stderr or result2.stderr}"
                )

        # Locate the skill folder inside the clone
        source = clone_dir / subpath if subpath else clone_dir

        if not source.exists():
            raise RuntimeError(
                f"Path '{subpath}' not found in {repo_slug}. "
                "Check that the URL points to an existing folder."
            )

        # Copy into user-skills, overwriting if it already exists
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(str(source), str(dest))
        logger.info("Installed skill '%s' from %s to %s", skill_name, url, dest)

    from erebus.skills.registry import refresh_registry

    refresh_registry()
    return dest


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
