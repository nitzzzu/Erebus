"""Agno Toolkit for workspace management.

Allows the agent to create, list, switch, update, and delete workspaces
(named project directories).  The current workspace scopes file and bash
operations to a specific project root.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

from erebus.config import get_settings

logger = logging.getLogger(__name__)

# Thread-local current workspace override (set per-run by agent.py)
_current_session_id: Optional[str] = None


def _get_manager():
    from erebus.workspace.manager import WorkspaceManager

    return WorkspaceManager(get_settings().data_dir)


class WorkspaceTools(Toolkit):
    """Agent tools for managing named project workspaces."""

    def __init__(self, session_id: Optional[str] = None) -> None:
        self._session_id = session_id
        super().__init__(name="workspace")
        self.register(self.create_workspace)
        self.register(self.list_workspaces)
        self.register(self.get_workspace)
        self.register(self.set_workspace)
        self.register(self.update_workspace)
        self.register(self.delete_workspace)

    def create_workspace(
        self,
        name: str,
        path: str,
        description: str = "",
    ) -> str:
        """Create a new named workspace pointing to a project directory.

        Parameters
        ----------
        name:
            Short identifier for the workspace (e.g. "my-api", "frontend").
        path:
            Absolute or ``~``-prefixed path to the project directory.
        description:
            Optional human-readable description of the project.

        Returns
        -------
        str
            Confirmation with workspace details, or an error message.
        """
        mgr = _get_manager()
        try:
            resolved = Path(path).expanduser().resolve()
            if not resolved.exists():
                return f"Path does not exist: {resolved}"
            ws = mgr.create(name, str(resolved), description)
            return (
                f"Workspace '{ws.name}' created.\n"
                f"  path: {ws.path}\n"
                f"  description: {ws.description or '(none)'}"
            )
        except ValueError as exc:
            return f"Error: {exc}"

    def list_workspaces(self) -> str:
        """List all configured workspaces.

        Returns
        -------
        str
            Formatted table of workspaces with name, path, and description.
        """
        mgr = _get_manager()
        workspaces = mgr.list()
        if not workspaces:
            return "No workspaces configured. Use create_workspace to add one."

        current = None
        if self._session_id:
            ws = mgr.get_session_workspace(self._session_id)
            if ws:
                current = ws.name

        lines = [f"{'Name':<20}  {'Path':<40}  Description"]
        lines.append("-" * 80)
        for ws in workspaces:
            marker = " *" if ws.name == current else ""
            lines.append(f"{ws.name + marker:<20}  {ws.path:<40}  {ws.description}")
        if current:
            lines.append("\n(* = active workspace for this session)")
        return "\n".join(lines)

    def get_workspace(self) -> str:
        """Get the current active workspace for this session.

        Returns
        -------
        str
            Details of the active workspace, or a message if none is set.
        """
        mgr = _get_manager()
        if not self._session_id:
            return "No session context — workspace not tracked."
        ws = mgr.get_session_workspace(self._session_id)
        if ws is None:
            return (
                "No workspace set for this session. "
                "Use set_workspace(name) to activate one, or list_workspaces() to see options."
            )
        exists = ws.resolved_path.exists()
        return (
            f"Active workspace: {ws.name}\n"
            f"  path: {ws.path}\n"
            f"  description: {ws.description or '(none)'}\n"
            f"  exists: {exists}"
        )

    def set_workspace(self, name: str) -> str:
        """Switch the current session to the named workspace.

        This causes subsequent file and shell operations to be scoped to
        the workspace's project directory.

        Parameters
        ----------
        name:
            Name of the workspace to activate.

        Returns
        -------
        str
            Confirmation or error message.
        """
        mgr = _get_manager()
        ws = mgr.get(name)
        if ws is None:
            return (
                f"Workspace '{name}' not found. "
                "Use list_workspaces() to see available workspaces or "
                "create_workspace() to add a new one."
            )
        if self._session_id:
            mgr.set_session_workspace(self._session_id, name)
        # Also update OS CWD so bash commands land in the right place
        try:
            os.chdir(ws.resolved_path)
        except OSError as exc:
            return f"Workspace '{name}' set but could not chdir: {exc}"
        return (
            f"Workspace switched to '{ws.name}'.\n"
            f"  path: {ws.path}\n"
            f"  description: {ws.description or '(none)'}"
        )

    def update_workspace(
        self,
        name: str,
        path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Update a workspace's path or description.

        Parameters
        ----------
        name:
            Name of the workspace to update.
        path:
            New directory path (optional).
        description:
            New description (optional).

        Returns
        -------
        str
            Updated workspace details or error message.
        """
        if path is None and description is None:
            return "No fields to update provided."
        mgr = _get_manager()
        if path is not None:
            resolved = Path(path).expanduser().resolve()
            if not resolved.exists():
                return f"Path does not exist: {resolved}"
            path = str(resolved)
        ws = mgr.update(name, path=path, description=description)
        if ws is None:
            return f"Workspace '{name}' not found."
        return (
            f"Workspace '{ws.name}' updated.\n"
            f"  path: {ws.path}\n"
            f"  description: {ws.description or '(none)'}"
        )

    def delete_workspace(self, name: str) -> str:
        """Delete a workspace by name.

        Parameters
        ----------
        name:
            Name of the workspace to delete.

        Returns
        -------
        str
            Confirmation or error message.
        """
        mgr = _get_manager()
        ok = mgr.delete(name)
        if not ok:
            return f"Workspace '{name}' not found."
        return f"Workspace '{name}' deleted."
