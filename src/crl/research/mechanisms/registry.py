"""Load mechanism registry (scientific objects of the lab)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crl.shared.config import project_root


def registry_path() -> Path:
    return project_root() / "research_kb" / "mechanism_registry.json"


def load_registry() -> dict[str, Any]:
    path = registry_path()
    if not path.exists():
        return {"version": 0, "mechanisms": [], "error": "missing registry"}
    return json.loads(path.read_text())


def ranked_mechanisms() -> list[dict[str, Any]]:
    reg = load_registry()
    mechs = list(reg.get("mechanisms") or [])
    return sorted(mechs, key=lambda m: (m.get("rank", 99), -float(m.get("ev") or 0)))
