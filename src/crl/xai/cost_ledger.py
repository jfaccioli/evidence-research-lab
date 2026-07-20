"""Track estimated API cost / call counts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CostLedger:
    path: Path
    entries: list[dict] = field(default_factory=list)

    def record(self, kind: str, units: float = 1.0, note: str = "") -> None:
        self.entries.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                "units": units,
                "note": note,
            }
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.entries, indent=2))

    def total_units(self) -> float:
        return float(sum(e.get("units", 0) for e in self.entries))
