"""Agno Toolkit for structured todo/task tracking.

Todos are scoped to a workspace (or a global default) and stored as a
JSON file.  The agent can read and atomically replace the todo list,
enabling structured multi-step planning and progress tracking.

Schema of each todo item::

    {
        "id": "1",
        "content": "Description of task",
        "status": "pending" | "in_progress" | "completed",
        "priority": "low" | "medium" | "high"
    }
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from threading import Lock
from typing import Optional

from agno.tools.toolkit import Toolkit

from erebus.config import get_settings

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"pending", "in_progress", "completed"}
_VALID_PRIORITIES = {"low", "medium", "high"}

_todo_lock = Lock()


def _todos_path(workspace_name: Optional[str] = None) -> Path:
    settings = get_settings()
    base = settings.data_dir / "todos"
    base.mkdir(parents=True, exist_ok=True)
    name = workspace_name or "_global"
    return base / f"{name}.json"


def _load_todos(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_todos(path: Path, todos: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(todos, indent=2), encoding="utf-8")


def _format_todos(todos: list[dict]) -> str:
    if not todos:
        return "No todos."
    status_icon = {"pending": "○", "in_progress": "◑", "completed": "●"}
    priority_tag = {"high": "[H]", "medium": "[M]", "low": "[L]"}
    lines = []
    for t in todos:
        sid = t.get("id", "?")
        icon = status_icon.get(t.get("status", "pending"), "○")
        pri = priority_tag.get(t.get("priority", "medium"), "[M]")
        content = t.get("content", "")
        lines.append(f"{icon} {pri} [{sid}] {content}")
    return "\n".join(lines)


class TodoTools(Toolkit):
    """Agent tools for managing a structured todo list per workspace."""

    def __init__(self, workspace_name: Optional[str] = None) -> None:
        self._workspace_name = workspace_name
        super().__init__(name="todo")
        self.register(self.read_todos)
        self.register(self.write_todos)
        self.register(self.add_todo)
        self.register(self.update_todo)
        self.register(self.delete_todo)
        self.register(self.clear_completed)

    def _path(self) -> Path:
        return _todos_path(self._workspace_name)

    def read_todos(self, status: Optional[str] = None) -> str:
        """Read the current todo list.

        Parameters
        ----------
        status:
            Optional filter: ``pending``, ``in_progress``, or ``completed``.
            If omitted, all todos are returned.

        Returns
        -------
        str
            Formatted list of todos.
        """
        with _todo_lock:
            todos = _load_todos(self._path())
        if status:
            todos = [t for t in todos if t.get("status") == status]
        return _format_todos(todos)

    def write_todos(self, todos: list[dict]) -> str:
        """Atomically replace the entire todo list.

        Use this to make bulk updates.  Each item must have ``content`` and
        optionally ``id``, ``status`` (default ``pending``), and ``priority``
        (default ``medium``).

        Parameters
        ----------
        todos:
            New list of todo items.

        Returns
        -------
        str
            Confirmation with count, or an error.
        """
        normalised = []
        for i, item in enumerate(todos):
            if not isinstance(item, dict) or not item.get("content"):
                return f"Item {i} missing required 'content' field."
            status = item.get("status", "pending")
            priority = item.get("priority", "medium")
            if status not in _VALID_STATUSES:
                valid = sorted(_VALID_STATUSES)
                return f"Item {i}: invalid status '{status}'. Must be one of {valid}."
            if priority not in _VALID_PRIORITIES:
                valid = sorted(_VALID_PRIORITIES)
                return f"Item {i}: invalid priority '{priority}'. Must be one of {valid}."
            normalised.append({
                "id": item.get("id") or str(i + 1),
                "content": item["content"],
                "status": status,
                "priority": priority,
            })
        with _todo_lock:
            _save_todos(self._path(), normalised)
        return f"Todo list updated: {len(normalised)} item(s).\n\n" + _format_todos(normalised)

    def add_todo(
        self,
        content: str,
        priority: str = "medium",
        status: str = "pending",
    ) -> str:
        """Add a single todo item to the list.

        Parameters
        ----------
        content:
            Description of the task.
        priority:
            ``low``, ``medium`` (default), or ``high``.
        status:
            ``pending`` (default), ``in_progress``, or ``completed``.

        Returns
        -------
        str
            Confirmation with the new item's id.
        """
        if priority not in _VALID_PRIORITIES:
            return f"Invalid priority '{priority}'. Choose from: {sorted(_VALID_PRIORITIES)}."
        if status not in _VALID_STATUSES:
            return f"Invalid status '{status}'. Choose from: {sorted(_VALID_STATUSES)}."
        new_id = uuid.uuid4().hex[:6]
        item = {"id": new_id, "content": content, "status": status, "priority": priority}
        with _todo_lock:
            todos = _load_todos(self._path())
            todos.append(item)
            _save_todos(self._path(), todos)
        return f"Todo added (id={new_id}): [{priority.upper()}] {content}"

    def update_todo(
        self,
        todo_id: str,
        content: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> str:
        """Update a todo item by id.

        Parameters
        ----------
        todo_id:
            The id of the todo item to update.
        content:
            New description (optional).
        status:
            New status: ``pending``, ``in_progress``, or ``completed`` (optional).
        priority:
            New priority: ``low``, ``medium``, or ``high`` (optional).

        Returns
        -------
        str
            Updated item or error message.
        """
        if status and status not in _VALID_STATUSES:
            return f"Invalid status '{status}'. Choose from: {sorted(_VALID_STATUSES)}."
        if priority and priority not in _VALID_PRIORITIES:
            return f"Invalid priority '{priority}'. Choose from: {sorted(_VALID_PRIORITIES)}."
        with _todo_lock:
            todos = _load_todos(self._path())
            for item in todos:
                if item.get("id") == todo_id:
                    if content is not None:
                        item["content"] = content
                    if status is not None:
                        item["status"] = status
                    if priority is not None:
                        item["priority"] = priority
                    _save_todos(self._path(), todos)
                    pri = item['priority'].upper()
                    return (
                        f"Todo '{todo_id}' updated: "
                        f"[{pri}] {item['content']} \u2014 {item['status']}"
                    )
        return f"Todo '{todo_id}' not found."

    def delete_todo(self, todo_id: str) -> str:
        """Delete a todo item by id.

        Parameters
        ----------
        todo_id:
            The id of the todo item to delete.

        Returns
        -------
        str
            Confirmation or error message.
        """
        with _todo_lock:
            todos = _load_todos(self._path())
            new_todos = [t for t in todos if t.get("id") != todo_id]
            if len(new_todos) == len(todos):
                return f"Todo '{todo_id}' not found."
            _save_todos(self._path(), new_todos)
        return f"Todo '{todo_id}' deleted."

    def clear_completed(self) -> str:
        """Remove all completed todos from the list.

        Returns
        -------
        str
            Confirmation with count of removed items.
        """
        with _todo_lock:
            todos = _load_todos(self._path())
            remaining = [t for t in todos if t.get("status") != "completed"]
            removed = len(todos) - len(remaining)
            _save_todos(self._path(), remaining)
        return f"Removed {removed} completed todo(s). {len(remaining)} remaining."
