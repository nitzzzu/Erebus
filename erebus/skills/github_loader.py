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

    Note
    ----
    Requires ``git`` to be installed and available on ``PATH``.
    """
    import re
    import tempfile

    # Parse the GitHub URL using a linear (non-backtracking) pattern.
    # https://github.com/{owner}/{repo}/tree/{ref}/{path}
    # Each captured segment is deliberately limited to avoid ReDoS.
    pattern = re.compile(
        r"https?://github\.com"
        r"/([A-Za-z0-9_.\-]+)"           # owner
        r"/([A-Za-z0-9_.\-]+)"           # repo
        r"(?:/tree/([A-Za-z0-9_.\-/]+))?"  # optional /tree/<ref>[/<path>]
        r"/?$"
    )
    m = pattern.match(url.rstrip("/"))
    if not m:
        raise ValueError(
            f"Cannot parse GitHub URL: {url!r}. "
            "Expected format: https://github.com/owner/repo/tree/branch/path/to/skill"
        )

    _tree_part = m.group(3) or ""
    repo_name = m.group(2)

    # Split tree_part into ref and optional subpath.
    # The ref is the first path segment; the rest is the subpath.
    tree_parts = [p for p in _tree_part.split("/") if p]
    ref = tree_parts[0] if tree_parts else ""
    subpath_parts = tree_parts[1:]

    # Validate that ref and subpath parts contain only safe characters and
    # start with an alphanumeric character (prevents flag-like or traversal values).
    _safe = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$")
    if ref and not _safe.match(ref):
        raise ValueError(f"Unsafe git ref: {ref!r}")
    for part in subpath_parts:
        if not _safe.match(part):
            raise ValueError(f"Unsafe path component: {part!r}")
        if part in (".", ".."):
            raise ValueError(f"Path traversal component not allowed: {part!r}")

    # Re-build subpath from the validated parts only — this breaks taint propagation.
    subpath = "/".join(subpath_parts)

    # Determine skill name from the last validated path component (or repo name).
    # Re-extract from the validated regex match to further break taint flow.
    if subpath_parts:
        skill_name = _safe.match(subpath_parts[-1]).group()  # type: ignore[union-attr]
    else:
        skill_name = _safe.match(repo_name).group()  # type: ignore[union-attr]

    # Validate skill_name for safe filesystem use
    if not _safe.match(skill_name):
        raise ValueError(f"Derived skill name is not safe for filesystem use: {skill_name!r}")

    settings = get_settings()
    user_skills_dir = settings.data_dir / "user-skills"
    user_skills_dir.mkdir(parents=True, exist_ok=True)
    dest = user_skills_dir / skill_name

    # Ensure dest is still within user_skills_dir (no traversal)
    try:
        dest.resolve().relative_to(user_skills_dir.resolve())
    except ValueError:
        raise ValueError(f"Skill name would escape user-skills directory: {skill_name!r}")

    # Build the clone URL from the regex-validated owner and repo name only.
    # Both variables are bound to group matches of [A-Za-z0-9_.\-]+ so they
    # cannot contain shell metacharacters or path traversal sequences.
    safe_owner = m.group(1)
    safe_repo = m.group(2)
    clone_url = f"https://github.com/{safe_owner}/{safe_repo}.git"

    # Use a temp directory for the sparse clone
    with tempfile.TemporaryDirectory(prefix="erebus-skill-") as tmpdir:
        clone_dir = Path(tmpdir) / "repo"

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

        # Write the sparse-checkout pattern (subpath is already validated above)
        sparse_file = clone_dir / ".git" / "info" / "sparse-checkout"
        sparse_file.parent.mkdir(parents=True, exist_ok=True)
        pattern_str = f"{subpath}/*\n" if subpath else "/*\n"
        sparse_file.write_text(pattern_str)

        # Pull the desired ref (or default branch).
        # `ref` has been validated to contain only safe characters; pass as
        # a separate argument so it is never interpreted as a shell flag.
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
                    f"Failed to fetch {safe_owner}/{safe_repo}: {result.stderr or result2.stderr}"
                )

        # Locate the skill folder inside the clone.
        # subpath is assembled only from parts validated to [A-Za-z0-9][A-Za-z0-9_.\-]*
        # so it cannot contain traversal sequences.
        source = (clone_dir / subpath).resolve() if subpath else clone_dir.resolve()

        # Guard: resolved source must still be inside the temp clone dir.
        try:
            source.relative_to(clone_dir.resolve())
        except ValueError:
            raise RuntimeError("Resolved source path escapes clone directory.")

        if not source.exists():
            raise RuntimeError(
                f"Path '{subpath}' not found in {safe_owner}/{safe_repo}. "
                "Check that the URL points to an existing folder."
            )

        # Copy into user-skills, overwriting if it already exists
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
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
