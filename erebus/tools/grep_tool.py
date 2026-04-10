"""Agno Toolkit for content search (grep / ripgrep).

Searches file contents using regex patterns.  Uses ``ripgrep`` (rg) when
available for speed; falls back to Python's ``re`` module otherwise.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_MAX_RESULTS = 200
_MAX_LINE_LEN = 500


def _rg_available() -> bool:
    """Return True if ripgrep is on PATH."""
    try:
        result = subprocess.run(
            ["rg", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


_HAS_RG: Optional[bool] = None


def _check_rg() -> bool:
    global _HAS_RG
    if _HAS_RG is None:
        _HAS_RG = _rg_available()
    return _HAS_RG


class GrepTools(Toolkit):
    """Agent tool for searching file contents with regular expressions."""

    def __init__(self, workspace_path: Optional[str] = None) -> None:
        self._workspace_path = workspace_path
        super().__init__(name="grep")
        self.register(self.grep)

    def _base(self) -> Path:
        if self._workspace_path:
            return Path(self._workspace_path)
        return Path(os.getcwd())

    def grep(
        self,
        pattern: str,
        path: Optional[str] = None,
        file_pattern: Optional[str] = None,
        case_insensitive: bool = False,
        context_lines: int = 0,
        max_results: int = _MAX_RESULTS,
    ) -> str:
        """Search file contents for a regular expression pattern.

        Uses ``rg`` (ripgrep) if available, otherwise pure Python.

        Parameters
        ----------
        pattern:
            Regular expression to search for.
        path:
            File or directory to search in.  Defaults to the active workspace
            root or current working directory.
        file_pattern:
            Optional glob pattern to restrict which files are searched,
            e.g. ``"*.py"`` or ``"*.{ts,tsx}"``.
        case_insensitive:
            If True, perform case-insensitive matching.
        context_lines:
            Number of lines of surrounding context to include (like ``grep -C``).
        max_results:
            Maximum number of matching lines to return.

        Returns
        -------
        str
            Matching lines in ``file:line:content`` format, or a message if
            nothing matched.
        """
        search_path = (
            Path(path).expanduser().resolve() if path else self._base()
        )
        if not search_path.exists():
            return f"Path not found: {search_path}"

        if _check_rg():
            return self._grep_rg(
                pattern, search_path, file_pattern, case_insensitive,
                context_lines, max_results,
            )
        return self._grep_python(
            pattern, search_path, file_pattern, case_insensitive,
            context_lines, max_results,
        )

    # ── ripgrep backend ───────────────────────────────────────────────────────

    def _grep_rg(
        self,
        pattern: str,
        search_path: Path,
        file_pattern: Optional[str],
        case_insensitive: bool,
        context_lines: int,
        max_results: int,
    ) -> str:
        cmd = ["rg", "--line-number", "--no-heading", "--color=never"]
        if case_insensitive:
            cmd.append("--ignore-case")
        if file_pattern:
            cmd.extend(["--glob", file_pattern])
        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])
        cmd.extend(["-m", str(max_results), "--", pattern, str(search_path)])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip()
            if not output:
                if result.returncode == 1:
                    return f"No matches for '{pattern}'."
                if result.stderr:
                    return f"ripgrep error: {result.stderr[:300]}"
                return f"No matches for '{pattern}'."
            # Relativise paths in output
            lines = output.split("\n")
            rel_lines = []
            for line in lines:
                # rg output: /abs/path/file:line:content  or  -- (separator)
                if line.startswith("--"):
                    rel_lines.append(line)
                    continue
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    try:
                        rel = str(Path(parts[0]).relative_to(search_path))
                        rel_lines.append(f"{rel}:{parts[1]}:{parts[2]}")
                        continue
                    except ValueError:
                        pass
                rel_lines.append(line)
            return "\n".join(rel_lines)
        except subprocess.TimeoutExpired:
            return "Search timed out."
        except Exception as exc:
            return f"Search error: {exc}"

    # ── Python fallback ───────────────────────────────────────────────────────

    def _grep_python(
        self,
        pattern: str,
        search_path: Path,
        file_pattern: Optional[str],
        case_insensitive: bool,
        context_lines: int,
        max_results: int,
    ) -> str:
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as exc:
            return f"Invalid regex pattern: {exc}"

        # Collect files to search
        if search_path.is_file():
            files = [search_path]
        else:
            files_iter = search_path.rglob(file_pattern or "*")
            files = [f for f in files_iter if f.is_file()]

        matches: list[str] = []
        for fpath in files:
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            lines = text.split("\n")
            for lineno, line in enumerate(lines, start=1):
                if regex.search(line):
                    try:
                        base = (
                            search_path.parent
                            if search_path.is_file()
                            else search_path
                        )
                        rel = str(fpath.relative_to(base))
                    except ValueError:
                        rel = str(fpath)
                    trunc_line = line[:_MAX_LINE_LEN]
                    if context_lines > 0:
                        start = max(0, lineno - 1 - context_lines)
                        end = min(len(lines), lineno + context_lines)
                        ctx = [f"{rel}:{i+1}:{lines[i][:_MAX_LINE_LEN]}" for i in range(start, end)]
                        matches.extend(ctx)
                        matches.append("--")
                    else:
                        matches.append(f"{rel}:{lineno}:{trunc_line}")
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break

        if not matches:
            return f"No matches for '{pattern}'."

        output = "\n".join(matches[:max_results])
        if len(matches) >= max_results:
            output += f"\n\n(results truncated at {max_results} matches)"
        return output
