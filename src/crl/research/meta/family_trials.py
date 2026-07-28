"""Family / programme trial ledger — multiplicity awareness (Workstream F P3).

Records how many exploratory hypotheses were evaluated per family_id and
programme. Does **not** change gates; makes selection burden visible.
Aligned with public multiple-testing literature (track trial counts).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root


def ledger_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "research_kb" / "family_trial_ledger.json"


def load_ledger(root: Path | None = None) -> dict[str, Any]:
    p = ledger_path(root)
    if not p.exists():
        return {
            "version": 1,
            "updated_at": None,
            "total_exploratory_trials": 0,
            "families": {},
            "programmes": {},
            "events": [],
        }
    return json.loads(p.read_text())


def save_ledger(ledger: dict[str, Any], root: Path | None = None) -> Path:
    p = ledger_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    ledger = dict(ledger)
    ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(ledger, indent=2) + "\n")
    return p


def record_programme_trials(
    *,
    programme: str,
    family_counts: dict[str, int],
    n_passed_val: int = 0,
    n_candidates: int = 0,
    dataset_id: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Add exploratory trial counts from a finished programme batch."""
    led = load_ledger(root)
    n_new = int(sum(family_counts.values()))
    led["total_exploratory_trials"] = int(led.get("total_exploratory_trials") or 0) + n_new

    families = dict(led.get("families") or {})
    for fam, n in family_counts.items():
        slot = dict(families.get(fam) or {"n_trials": 0, "n_programmes": 0})
        slot["n_trials"] = int(slot.get("n_trials") or 0) + int(n)
        slot["n_programmes"] = int(slot.get("n_programmes") or 0) + 1
        slot["last_programme"] = programme
        families[fam] = slot
    led["families"] = families

    programmes = dict(led.get("programmes") or {})
    programmes[programme] = {
        "n_trials": n_new,
        "family_counts": family_counts,
        "n_passed_val": int(n_passed_val),
        "n_candidates": int(n_candidates),
        "dataset_id": dataset_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    led["programmes"] = programmes

    events = list(led.get("events") or [])
    events.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "programme": programme,
            "n_trials": n_new,
            "n_passed_val": n_passed_val,
            "n_candidates": n_candidates,
        }
    )
    led["events"] = events[-200:]
    save_ledger(led, root)
    return {
        "programme": programme,
        "n_trials_added": n_new,
        "total_exploratory_trials": led["total_exploratory_trials"],
        "n_families_tracked": len(families),
    }


def multiplicity_snapshot(root: Path | None = None) -> dict[str, Any]:
    """Compact view for CLI / status."""
    led = load_ledger(root)
    fams = led.get("families") or {}
    top = sorted(
        ((k, v.get("n_trials", 0)) for k, v in fams.items()),
        key=lambda x: -int(x[1]),
    )[:15]
    total = int(led.get("total_exploratory_trials") or 0)
    # Soft warning thresholds (informational — not gates)
    warn = total >= 50
    return {
        "total_exploratory_trials": total,
        "n_families": len(fams),
        "top_families_by_trials": [{"family_id": a, "n_trials": b} for a, b in top],
        "selection_burden_warning": warn,
        "message": (
            f"{total} exploratory trials across {len(fams)} families. "
            + (
                "Elevated selection burden — prefer new mechanisms, not clones."
                if warn
                else "Multiplicity ledger active."
            )
        ),
    }
