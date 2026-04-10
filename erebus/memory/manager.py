"""High-level memory helpers wrapping Agno's MemoryManager.

Provides CRUD operations for the REST API and CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

from erebus.config import ErebusSettings, get_settings


@dataclass
class MemoryEntry:
    """Lightweight representation of a stored memory."""

    id: str
    content: str
    topics: list[str]
    user_id: str


class ErebusMemory:
    """Facade over Agno MemoryManager for Erebus-specific operations."""

    def __init__(self, settings: Optional[ErebusSettings] = None) -> None:
        if settings is None:
            settings = get_settings()
        self._db = SqliteDb(db_file=settings.db_path)
        self._manager = MemoryManager(model=settings.default_model, db=self._db)

    @property
    def manager(self) -> MemoryManager:
        return self._manager

    @property
    def db(self) -> SqliteDb:
        return self._db

    def list_memories(self, user_id: str) -> list[dict]:
        """Return all memories for *user_id* from the database."""
        rows = self._db.get_user_memories(user_id=user_id)
        if not rows:
            return []
        return [
            {
                "id": str(r.id) if hasattr(r, "id") else "",
                "content": r.memory if hasattr(r, "memory") else str(r),
                "topics": r.topics if hasattr(r, "topics") else [],
            }
            for r in rows
        ]

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by its ID."""
        try:
            self._db.delete_user_memory(memory_id=memory_id)
            return True
        except Exception:
            return False
