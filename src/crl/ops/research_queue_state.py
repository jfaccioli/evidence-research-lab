"""Machine-readable research queue state (complements docs/RESEARCH_QUEUE.md)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root

DEFAULT_STATE = {
    "version": 1,
    "updated_at": None,
    "policy": "no_low_ev_free_btc_technical_clones",
    "active": [],
    "blocked": [
        {
            "id": "HUMAN_VENDOR_PIT",
            "reason": "paid/export vendor-grade series needs human",
        },
        {
            "id": "X_SOCIAL_PIT",
            "reason": "needs reconstructible archive",
        },
    ],
    "completed": [],
    "capability_backlog": [
        "programme INDEX external attach + run-programme wiring",
        "series inventory CLI",
        "new-programme scaffold",
        "series readiness checklist",
    ],
}


def state_path(root: Path | None = None) -> Path:
    root = root or project_root()
    return root / "research_kb" / "research_queue_state.json"


def load_queue_state(root: Path | None = None) -> dict[str, Any]:
    p = state_path(root)
    if not p.exists():
        st = dict(DEFAULT_STATE)
        st["updated_at"] = datetime.now(timezone.utc).isoformat()
        return st
    return json.loads(p.read_text())


def save_queue_state(state: dict[str, Any], root: Path | None = None) -> Path:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    return p


def record_programme_result(
    programme_id: str,
    *,
    n_passed_val: int,
    n_run: int,
    n_candidates: int,
    notes: str = "",
) -> dict[str, Any]:
    st = load_queue_state()
    entry = {
        "id": programme_id,
        "n_passed_val": n_passed_val,
        "n_run": n_run,
        "n_candidates": n_candidates,
        "notes": notes,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    completed = list(st.get("completed") or [])
    completed = [c for c in completed if c.get("id") != programme_id]
    completed.append(entry)
    st["completed"] = completed[-50:]
    save_queue_state(st)
    return entry
