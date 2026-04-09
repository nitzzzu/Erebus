"""Session management for Erebus WebUI.

Provides persistent session storage (JSON files) with in-memory LRU cache,
session CRUD operations, and compact session listing.
"""

from __future__ import annotations

import json
import time
import uuid
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Optional


@dataclass
class Session:
    """A single chat session."""

    session_id: str
    title: str
    model: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    pinned: bool = False
    archived: bool = False
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    def compact(self) -> dict[str, Any]:
        """Return metadata-only dict (no messages) for list views."""
        d = asdict(self)
        d.pop("messages", None)
        d.pop("tool_calls", None)
        d["message_count"] = len(self.messages)
        return d


_MAX_CACHE = 100
_sessions: OrderedDict[str, Session] = OrderedDict()
_lock = Lock()


def _sessions_dir(data_dir: Path) -> Path:
    d = data_dir / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session_path(data_dir: Path, sid: str) -> Path:
    return _sessions_dir(data_dir) / f"{sid}.json"


def save_session(data_dir: Path, session: Session) -> None:
    """Persist session to disk and update cache."""
    session.updated_at = time.time()
    path = _session_path(data_dir, session.session_id)
    path.write_text(json.dumps(asdict(session), default=str), encoding="utf-8")
    with _lock:
        _sessions[session.session_id] = session
        _sessions.move_to_end(session.session_id)
        while len(_sessions) > _MAX_CACHE:
            _sessions.popitem(last=False)


def load_session(data_dir: Path, sid: str) -> Optional[Session]:
    """Load session from cache or disk."""
    with _lock:
        if sid in _sessions:
            _sessions.move_to_end(sid)
            return _sessions[sid]

    path = _session_path(data_dir, sid)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        # Validate required fields exist
        if "session_id" not in raw or "title" not in raw or "model" not in raw:
            return None
        filtered = {k: v for k, v in raw.items() if k in Session.__dataclass_fields__}
        session = Session(**filtered)
        with _lock:
            _sessions[sid] = session
            while len(_sessions) > _MAX_CACHE:
                _sessions.popitem(last=False)
        return session
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def new_session(data_dir: Path, model: str, title: str = "New Chat") -> Session:
    """Create and persist a new session."""
    sid = uuid.uuid4().hex[:12]
    session = Session(session_id=sid, title=title, model=model)
    save_session(data_dir, session)
    return session


def delete_session(data_dir: Path, sid: str) -> bool:
    """Delete a session from disk and cache."""
    with _lock:
        _sessions.pop(sid, None)
    path = _session_path(data_dir, sid)
    if path.exists():
        path.unlink()
        return True
    return False


def all_sessions(data_dir: Path) -> list[dict[str, Any]]:
    """Return compact metadata for all sessions, sorted by updated_at desc."""
    sessions_dir = _sessions_dir(data_dir)
    result = []
    for path in sessions_dir.glob("*.json"):
        sid = path.stem
        session = load_session(data_dir, sid)
        if session:
            result.append(session.compact())
    result.sort(key=lambda s: s["updated_at"], reverse=True)
    return result


def rename_session(data_dir: Path, sid: str, title: str) -> Optional[Session]:
    """Rename a session."""
    session = load_session(data_dir, sid)
    if session is None:
        return None
    session.title = title
    save_session(data_dir, session)
    return session
