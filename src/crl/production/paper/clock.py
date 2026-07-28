"""Paper-clock mandate records for APPROVED survivors.

Historical ``crl paper`` sessions harden the execution path; the paper *clock*
is a separate, explicit record that a confirmatory survivor has been walked
under mandate limits for a pre-agreed window before shadow / Phase-5.

These records live under ``data/paper_clock/`` and are **ops artifacts**, not
research promotion gates. Science gates stay frozen in configs/default.yaml.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from crl.production.strategies import list_approved

DEFAULT_MIN_CALENDAR_DAYS = 30
CLOCK_DIR_NAME = "paper_clock"


def default_clock_dir(project_root: Path) -> Path:
    return project_root / "data" / CLOCK_DIR_NAME


@dataclass
class PaperClockRecord:
    """Mandate paper-clock state for one APPROVED strategy_id."""

    strategy_id: str
    started_at: str
    min_calendar_days: int = DEFAULT_MIN_CALENDAR_DAYS
    sessions: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    status: str = "in_progress"  # in_progress | complete

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PaperClockRecord":
        return cls(
            strategy_id=str(d["strategy_id"]),
            started_at=str(d["started_at"]),
            min_calendar_days=int(d.get("min_calendar_days", DEFAULT_MIN_CALENDAR_DAYS)),
            sessions=list(d.get("sessions") or []),
            notes=list(d.get("notes") or []),
            status=str(d.get("status") or "in_progress"),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clock_path(clock_dir: Path, strategy_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in strategy_id)
    return clock_dir / f"{safe}.json"


def load_clock(clock_dir: Path, strategy_id: str) -> Optional[PaperClockRecord]:
    p = clock_path(clock_dir, strategy_id)
    if not p.exists():
        return None
    return PaperClockRecord.from_dict(json.loads(p.read_text()))


def save_clock(clock_dir: Path, rec: PaperClockRecord) -> Path:
    clock_dir.mkdir(parents=True, exist_ok=True)
    p = clock_path(clock_dir, rec.strategy_id)
    p.write_text(json.dumps(rec.to_dict(), indent=2, sort_keys=True) + "\n")
    return p


def start_or_get_clock(
    clock_dir: Path,
    strategy_id: str,
    *,
    min_calendar_days: int = DEFAULT_MIN_CALENDAR_DAYS,
) -> PaperClockRecord:
    existing = load_clock(clock_dir, strategy_id)
    if existing is not None:
        return existing
    rec = PaperClockRecord(
        strategy_id=strategy_id,
        started_at=_now_iso(),
        min_calendar_days=min_calendar_days,
        notes=["Opened via paper clock API; not a science promotion."],
    )
    save_clock(clock_dir, rec)
    return rec


def record_session(
    clock_dir: Path,
    strategy_id: str,
    *,
    n_bars: int,
    n_fills: int,
    equity_end: float | None,
    max_drawdown: float | None,
    journal_path: str | None = None,
    mandate_limits: bool = True,
    min_calendar_days: int = DEFAULT_MIN_CALENDAR_DAYS,
) -> PaperClockRecord:
    """Append one paper session and recompute complete status."""
    rec = start_or_get_clock(
        clock_dir, strategy_id, min_calendar_days=min_calendar_days
    )
    rec.sessions.append(
        {
            "recorded_at": _now_iso(),
            "n_bars": int(n_bars),
            "n_fills": int(n_fills),
            "equity_end": equity_end,
            "max_drawdown": max_drawdown,
            "journal_path": journal_path,
            "mandate_limits": bool(mandate_limits),
        }
    )
    rec.status = "complete" if _is_complete(rec) else "in_progress"
    save_clock(clock_dir, rec)
    return rec


def _is_complete(rec: PaperClockRecord) -> bool:
    if not rec.sessions:
        return False
    # At least one mandate-limited session required
    if not any(s.get("mandate_limits") for s in rec.sessions):
        return False
    try:
        started = datetime.fromisoformat(rec.started_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    now = datetime.now(timezone.utc)
    elapsed = (now - started).total_seconds() / 86400.0
    return elapsed >= float(rec.min_calendar_days) and len(rec.sessions) >= 1


def paper_clock_satisfied(
    clock_dir: Path,
    *,
    strategy_ids: list[str] | None = None,
    min_survivors: int = 2,
) -> dict[str, Any]:
    """Check whether APPROVED (or given) ids have complete paper clocks.

    Returns a readiness-friendly dict. Never invents survivors.
    """
    ids = list(strategy_ids) if strategy_ids is not None else list_approved()
    if len(ids) < min_survivors:
        return {
            "ok": False,
            "reason": f"need ≥{min_survivors} APPROVED survivors; have {len(ids)}",
            "n_approved": len(ids),
            "complete": [],
            "incomplete": ids,
        }
    complete: list[str] = []
    incomplete: list[str] = []
    for sid in ids:
        rec = load_clock(clock_dir, sid)
        if rec is not None and rec.status == "complete" and _is_complete(rec):
            complete.append(sid)
        else:
            incomplete.append(sid)
    return {
        "ok": len(complete) >= min_survivors and not incomplete,
        "reason": (
            "paper clocks complete on all listed survivors"
            if len(complete) >= min_survivors and not incomplete
            else "paper clock incomplete or missing for some survivors"
        ),
        "n_approved": len(ids),
        "complete": complete,
        "incomplete": incomplete,
    }
