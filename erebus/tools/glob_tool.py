"""Agno Toolkit for glob-based file discovery.

Provides fast pattern-based file search respecting the active workspace.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_MAX_RESULTS = 500


class GlobTools(Toolkit):
    """Agent tool for finding files by glob pattern."""

    def __init__(self, workspace_path: Optional[str] = None) -> None:
        self._workspace_path = workspace_path
        super().__init__(name="glob")
        self.register(self.glob)

    def _base(self) -> Path:
        if self._workspace_path:
            return Path(self._workspace_path)
        return Path(os.getcwd())

    def glob(
        self,
        pattern: str,
        base_dir: Optional[str] = None,
        max_results: int = _MAX_RESULTS,
    ) -> str:
        """Find files matching a glob pattern.

        Supports ``**`` for recursive matching, ``*`` for single-level, and
        ``?`` for single character.

        Examples::

            glob("**/*.py")               # all Python files recursively
            glob("src/**/*.ts")           # TypeScript files under src/
            glob("*.md", base_dir="docs") # Markdown files in docs/
            glob("**/*test*")             # files with "test" in the name

        Parameters
        ----------
        pattern:
            Glob pattern to match against.
        base_dir:
            Optional base directory.  Defaults to the active workspace root
            (or current working directory if no workspace is set).
        max_results:
            Maximum number of results to return (default 500).

        Returns
        -------
        str
            Newline-separated list of matching relative paths, or a message if
            no matches are found.
        """
        root = Path(base_dir).expanduser().resolve() if base_dir else self._base()
        if not root.exists():
            return f"Directory not found: {root}"

        try:
            matches = sorted(root.glob(pattern))
        except Exception as exc:
            return f"Glob error: {exc}"

        if not matches:
            return f"No files match pattern '{pattern}' in {root}"

        truncated = matches[:max_results]
        rel_paths = []
        for p in truncated:
            try:
                rel_paths.append(str(p.relative_to(root)))
            except ValueError:
                rel_paths.append(str(p))

        result = "\n".join(rel_paths)
        if len(matches) > max_results:
            result += (
                f"\n\n(showing {max_results} of {len(matches)} matches"
                " \u2014 refine the pattern to narrow results)"
            )
        return result
