"""Workspace manager for Erebus.

A workspace is a named project directory the agent operates within.
Workspaces are persisted in ~/.erebus/workspaces.json and a current
workspace per session is tracked in a lightweight in-memory registry.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)

# Per-session current workspace name: session_id -> workspace_name
_session_workspaces: dict[str, str] = {}
_sw_lock = Lock()


@dataclass
class Workspace:
    """A named project workspace."""

    name: str
    path: str
    description: str = ""
    created_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def resolved_path(self) -> Path:
        return Path(self.path).expanduser().resolve()


class WorkspaceManager:
    """CRUD manager for workspaces stored in a JSON file."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._store_path = data_dir / "workspaces.json"
        self._lock = Lock()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> dict[str, dict]:
        if not self._store_path.exists():
            return {}
        try:
            raw = json.loads(self._store_path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def _safe_path(path: str) -> Path:
        """Resolve and validate a workspace path.

        Raises ValueError if the path is not absolute after resolution
        or does not exist.
        """
        resolved = Path(path).expanduser().resolve()
        if not resolved.is_absolute():
            raise ValueError(f"Workspace path must be absolute: {resolved}")
        return resolved

    def _workspace_from_dict(self, raw: dict) -> Optional["Workspace"]:
        """Construct a Workspace from a raw dict, ignoring unknown keys."""
        try:
            fields = Workspace.__dataclass_fields__
            return Workspace(**{k: v for k, v in raw.items() if k in fields})
        except TypeError:
            return None

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create(self, name: str, path: str, description: str = "") -> Workspace:
        """Create a new workspace.  Raises ValueError if name already exists."""
        resolved = self._safe_path(path)
        with self._lock:
            data = self._load()
            if name in data:
                raise ValueError(f"Workspace '{name}' already exists.")
            ws = Workspace(name=name, path=str(resolved), description=description)
            data[name] = ws.as_dict()
            self._save(data)
        return ws

    def get(self, name: str) -> Optional[Workspace]:
        """Return a workspace by name, or None if not found."""
        with self._lock:
            data = self._load()
        raw = data.get(name)
        if raw is None:
            return None
        return self._workspace_from_dict(raw)

    def list(self) -> list[Workspace]:
        """Return all workspaces sorted by name."""
        with self._lock:
            data = self._load()
        workspaces = []
        for raw in data.values():
            ws = self._workspace_from_dict(raw)
            if ws is not None:
                workspaces.append(ws)
        return sorted(workspaces, key=lambda w: w.name)

    def delete(self, name: str) -> bool:
        """Delete a workspace by name.  Returns True if deleted, False if not found."""
        with self._lock:
            data = self._load()
            if name not in data:
                return False
            del data[name]
            self._save(data)
        return True

    def update(
        self,
        name: str,
        path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Workspace]:
        """Update workspace fields.  Returns updated workspace or None."""
        with self._lock:
            data = self._load()
            if name not in data:
                return None
            raw = data[name]
            if path is not None:
                resolved = self._safe_path(path)
                raw["path"] = str(resolved)
            if description is not None:
                raw["description"] = description
            data[name] = raw
            self._save(data)
        return self.get(name)

    # ── Auto-discovery ───────────────────────────────────────────────────────

    def sync_from_dir(self, workspaces_dir: Path) -> list[Workspace]:
        """Scan *workspaces_dir* for subdirectories and auto-register any that
        are not already in the store.  If no workspaces exist at all, a default
        ``main`` workspace is created.  Returns the full merged workspace list."""
        workspaces_dir.mkdir(parents=True, exist_ok=True)
        with self._lock:
            data = self._load()
            for entry in sorted(workspaces_dir.iterdir()):
                if entry.is_dir() and entry.name not in data:
                    ws = Workspace(name=entry.name, path=str(entry.resolve()))
                    data[entry.name] = ws.as_dict()
            if not data:
                main_path = workspaces_dir / "main"
                main_path.mkdir(exist_ok=True)
                ws = Workspace(name="main", path=str(main_path.resolve()), description="Default workspace")
                data["main"] = ws.as_dict()
            self._save(data)
        return self.list()

    # ── Session workspace tracking ────────────────────────────────────────────

    def set_session_workspace(self, session_id: str, name: str) -> None:
        """Associate a session with a workspace name."""
        with _sw_lock:
            _session_workspaces[session_id] = name

    def get_session_workspace(self, session_id: str) -> Optional[Workspace]:
        """Return the workspace associated with a session, or None."""
        with _sw_lock:
            name = _session_workspaces.get(session_id)
        if name is None:
            return None
        return self.get(name)

    def clear_session_workspace(self, session_id: str) -> None:
        """Remove session → workspace association."""
        with _sw_lock:
            _session_workspaces.pop(session_id, None)
