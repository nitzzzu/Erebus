"""Cron scheduler wrapping Agno's ScheduleManager.

Provides CRUD operations for scheduled tasks and a background runner
that evaluates cron expressions and triggers agent runs.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from croniter import croniter

from erebus.config import ErebusSettings, get_settings


@dataclass
class ScheduleEntry:
    """A single cron schedule."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    cron: str = "0 * * * *"
    description: str = ""
    enabled: bool = True
    payload: dict[str, Any] = field(default_factory=dict)
    timezone: str = "UTC"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_run: Optional[str] = None


class ErebusScheduler:
    """File-backed cron scheduler for Erebus.

    Schedules are persisted as JSON in ``~/.erebus/schedules.json``.
    """

    def __init__(self, settings: Optional[ErebusSettings] = None) -> None:
        if settings is None:
            settings = get_settings()
        self._path: Path = settings.data_dir / "schedules.json"
        self._schedules: list[ScheduleEntry] = self._load()

    # -- Persistence ----------------------------------------------------------

    def _load(self) -> list[ScheduleEntry]:
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                return [ScheduleEntry(**entry) for entry in raw]
            except Exception:
                return []
        return []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([asdict(s) for s in self._schedules], indent=2)
        )

    # -- CRUD -----------------------------------------------------------------

    def list(self, *, enabled: Optional[bool] = None) -> list[ScheduleEntry]:
        if enabled is None:
            return list(self._schedules)
        return [s for s in self._schedules if s.enabled == enabled]

    def get(self, schedule_id: str) -> Optional[ScheduleEntry]:
        return next((s for s in self._schedules if s.id == schedule_id), None)

    def create(
        self,
        name: str,
        cron: str,
        description: str = "",
        payload: Optional[dict[str, Any]] = None,
        timezone: str = "UTC",
    ) -> ScheduleEntry:
        # Validate cron expression
        if not croniter.is_valid(cron):
            raise ValueError(f"Invalid cron expression: {cron}")
        entry = ScheduleEntry(
            name=name,
            cron=cron,
            description=description,
            payload=payload or {},
            timezone=timezone,
        )
        self._schedules.append(entry)
        self._save()
        return entry

    def update(self, schedule_id: str, **kwargs: Any) -> Optional[ScheduleEntry]:
        entry = self.get(schedule_id)
        if entry is None:
            return None
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        self._save()
        return entry

    def delete(self, schedule_id: str) -> bool:
        before = len(self._schedules)
        self._schedules = [s for s in self._schedules if s.id != schedule_id]
        if len(self._schedules) < before:
            self._save()
            return True
        return False

    def enable(self, schedule_id: str) -> Optional[ScheduleEntry]:
        return self.update(schedule_id, enabled=True)

    def disable(self, schedule_id: str) -> Optional[ScheduleEntry]:
        return self.update(schedule_id, enabled=False)

    def get_due_schedules(self) -> list[ScheduleEntry]:
        """Return all enabled schedules that are due to run now."""
        now = datetime.now(timezone.utc)
        due: list[ScheduleEntry] = []
        for entry in self._schedules:
            if not entry.enabled:
                continue
            cron = croniter(entry.cron, now)
            prev = cron.get_prev(datetime)
            # Consider "due" if last_run is before prev trigger time
            if entry.last_run is None or datetime.fromisoformat(entry.last_run) < prev:
                due.append(entry)
        return due
