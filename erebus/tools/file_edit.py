"""Agno Toolkit for precise file editing.

Provides targeted file editing operations:
- ``view_file``        – view file contents with line numbers
- ``str_replace``      – find-and-replace an exact string in a file
- ``insert_lines``     – insert text after a specific line number
- ``delete_lines``     – remove a range of lines from a file
- ``create_file``      – create a new file (error if exists)
- ``append_to_file``   – append content to a file

These are complementary to Agno's built-in FileTools (which cover
reading/writing whole files) and give the agent surgical precision.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_MAX_VIEW_LINES = 500


def _resolve(path: str, workspace_path: Optional[str]) -> Path:
    p = Path(path).expanduser()
    if p.is_absolute():
        return p
    if workspace_path:
        return (Path(workspace_path) / p).resolve()
    return (Path(os.getcwd()) / p).resolve()


class FileEditTools(Toolkit):
    """Agent tools for precise, surgical file editing."""

    def __init__(self, workspace_path: Optional[str] = None) -> None:
        self._workspace_path = workspace_path
        super().__init__(name="file_edit")
        self.register(self.view_file)
        self.register(self.str_replace)
        self.register(self.insert_lines)
        self.register(self.delete_lines)
        self.register(self.create_file)
        self.register(self.append_to_file)

    def view_file(
        self,
        path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> str:
        """View file contents with line numbers.

        Parameters
        ----------
        path:
            Path to the file (relative to workspace root or absolute).
        start_line:
            First line to display (1-indexed, default: 1).
        end_line:
            Last line to display (default: start_line + 500).

        Returns
        -------
        str
            File contents with line numbers, or an error message.
        """
        fpath = _resolve(path, self._workspace_path)
        if not fpath.exists():
            return f"File not found: {path}"
        if fpath.is_dir():
            return f"Path is a directory: {path}"
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"Error reading file: {exc}"

        lines = text.split("\n")
        total = len(lines)
        s = max(1, start_line or 1)
        e = min(total, end_line or (s + _MAX_VIEW_LINES - 1))

        numbered = []
        for i, line in enumerate(lines[s - 1 : e], start=s):
            numbered.append(f"{i:>6}\t{line}")

        header = f"File: {path} (lines {s}–{e} of {total})"
        result = header + "\n" + "─" * len(header) + "\n" + "\n".join(numbered)
        if e < total:
            more_msg = (
                f"[Showing {e - s + 1} of {total} lines."
                " Use start_line/end_line to view more.]"
            )
            result += f"\n\n{more_msg}"
        return result

    def str_replace(
        self,
        path: str,
        old_str: str,
        new_str: str,
        count: int = 1,
    ) -> str:
        """Replace an exact string in a file.

        The ``old_str`` must match exactly (including whitespace and
        indentation).  Use ``count=-1`` to replace all occurrences.

        Parameters
        ----------
        path:
            Path to the file.
        old_str:
            Exact text to search for.  Must appear in the file.
        new_str:
            Replacement text.
        count:
            Number of occurrences to replace (default 1; use -1 for all).

        Returns
        -------
        str
            Confirmation with the number of replacements, or an error.
        """
        fpath = _resolve(path, self._workspace_path)
        if not fpath.exists():
            return f"File not found: {path}"
        try:
            original = fpath.read_text(encoding="utf-8")
        except OSError as exc:
            return f"Error reading file: {exc}"

        if old_str not in original:
            # Provide context to help the user identify the issue
            return (
                f"String not found in {path}.\n"
                "Tip: use view_file() to check the exact text including whitespace and indentation."
            )

        # str.replace(old, new, count) treats count=-1 as "replace all" in Python 3
        updated = original.replace(old_str, new_str, count)
        replaced = original.count(old_str) if count == -1 else min(count, original.count(old_str))

        try:
            fpath.write_text(updated, encoding="utf-8")
        except OSError as exc:
            return f"Error writing file: {exc}"
        return f"Replaced {replaced} occurrence(s) of the target string in {path}."

    def insert_lines(
        self,
        path: str,
        after_line: int,
        content: str,
    ) -> str:
        """Insert text after a specific line number.

        Parameters
        ----------
        path:
            Path to the file.
        after_line:
            Insert after this 1-indexed line number.  Use 0 to insert at the
            beginning of the file.
        content:
            Text to insert.  A trailing newline is added automatically.

        Returns
        -------
        str
            Confirmation or error message.
        """
        fpath = _resolve(path, self._workspace_path)
        if not fpath.exists():
            return f"File not found: {path}"
        try:
            text = fpath.read_text(encoding="utf-8")
        except OSError as exc:
            return f"Error reading file: {exc}"

        lines = text.split("\n")
        total = len(lines)
        if after_line < 0 or after_line > total:
            return (
                f"Line {after_line} is out of range "
                f"(file has {total} lines, use 0 to insert at start)."
            )

        insert_lines = content.splitlines()
        lines[after_line:after_line] = insert_lines
        try:
            fpath.write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            return f"Error writing file: {exc}"
        return f"Inserted {len(insert_lines)} line(s) after line {after_line} in {path}."

    def delete_lines(
        self,
        path: str,
        start_line: int,
        end_line: int,
    ) -> str:
        """Delete a range of lines from a file (inclusive).

        Parameters
        ----------
        path:
            Path to the file.
        start_line:
            First line to delete (1-indexed).
        end_line:
            Last line to delete (1-indexed, inclusive).

        Returns
        -------
        str
            Confirmation or error message.
        """
        fpath = _resolve(path, self._workspace_path)
        if not fpath.exists():
            return f"File not found: {path}"
        try:
            text = fpath.read_text(encoding="utf-8")
        except OSError as exc:
            return f"Error reading file: {exc}"

        lines = text.split("\n")
        total = len(lines)
        if start_line < 1 or end_line < start_line or start_line > total:
            return (
                f"Invalid range {start_line}–{end_line} (file has {total} lines). "
                "Lines are 1-indexed and start_line must be ≤ end_line."
            )
        end_line = min(end_line, total)
        del lines[start_line - 1 : end_line]
        try:
            fpath.write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            return f"Error writing file: {exc}"
        deleted = end_line - start_line + 1
        return f"Deleted {deleted} line(s) ({start_line}–{end_line}) from {path}."

    def create_file(self, path: str, content: str = "") -> str:
        """Create a new file with the given content.

        Fails if the file already exists (use FileTools.save_file with
        ``overwrite=True`` to overwrite).  Parent directories are created
        automatically.

        Parameters
        ----------
        path:
            Path to the new file.
        content:
            Initial content (default: empty).

        Returns
        -------
        str
            Confirmation or error message.
        """
        fpath = _resolve(path, self._workspace_path)
        if fpath.exists():
            return (
                f"File already exists: {path}. "
                "Use str_replace or FileTools.save_file to modify it."
            )
        try:
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")
        except OSError as exc:
            return f"Error creating file: {exc}"
        return f"File created: {path} ({len(content)} bytes)"

    def append_to_file(self, path: str, content: str) -> str:
        """Append content to an existing file.

        Parameters
        ----------
        path:
            Path to the file.
        content:
            Text to append.

        Returns
        -------
        str
            Confirmation or error message.
        """
        fpath = _resolve(path, self._workspace_path)
        if not fpath.exists():
            return f"File not found: {path}. Use create_file to create a new file."
        try:
            with fpath.open("a", encoding="utf-8") as f:
                f.write(content)
        except OSError as exc:
            return f"Error appending to file: {exc}"
        return f"Appended {len(content)} bytes to {path}."
