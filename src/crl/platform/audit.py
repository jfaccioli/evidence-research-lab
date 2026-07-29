"""Audit and replay helpers for platform runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class AuditEvent:
    ts: str
    event: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLog:
    run_id: str
    strategy_id: str
    mode: str
    events: list[AuditEvent] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def add(self, event: str, **payload: Any) -> None:
        self.events.append(
            AuditEvent(
                ts=datetime.now(timezone.utc).isoformat(),
                event=event,
                payload=payload,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "mode": self.mode,
            "meta": self.meta,
            "n_events": len(self.events),
            "events": [asdict(e) for e in self.events],
        }

    def write(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))
        return path


def load_audit(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())
