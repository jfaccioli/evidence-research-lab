"""Phase 1 completion criteria and hard research budget.

Architecture is frozen. This module exists so Phase 1 always reaches a
scientifically meaningful conclusion (A / B / C) rather than inventing
the next mechanism forever.

See docs/PHASE1_COMPLETION_CRITERIA.md.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root

ALLOWED_CONCLUSIONS = (
    "A_deployable_candidate_path",
    "B_richer_data_justified",
    "C_unlikely_robust_edge_under_constraints",
)

CONCLUSION_LABELS = {
    "A_deployable_candidate_path": (
        "A strategy (or risk policy) passed confirmatory under frozen gates "
        "and is eligible for live-data shadow under existing dual-track rules."
    ),
    "B_richer_data_justified": (
        "Budgeted programmes null'd on obtainable data, and EIR ranks a "
        "specific paid dataset with EV above remaining free options. "
        "Human decides whether to fund Phase 1b or stop."
    ),
    "C_unlikely_robust_edge_under_constraints": (
        "Under Phase 1 constraints (BTC spot, long/flat, no leverage, "
        "daily/4h admissible data within budget), we did not find a "
        "confirmatory-grade edge. Public/free-style daily prediction under "
        "our gates is unlikely to contain a sufficiently robust, deployable "
        "advantage without a qualitatively richer information class or a "
        "material change of mandate."
    ),
}


def budget_path() -> Path:
    return project_root() / "research_kb" / "rd" / "phase1_budget.json"


def load_budget() -> dict[str, Any]:
    p = budget_path()
    if not p.exists():
        return {
            "version": 0,
            "phase": "1",
            "architecture_frozen": True,
            "caps": {},
            "usage": {},
            "remaining": {},
            "phase1_conclusion": None,
            "allowed_conclusions": list(ALLOWED_CONCLUSIONS),
        }
    return json.loads(p.read_text())


def save_budget(obj: dict[str, Any]) -> Path:
    p = budget_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")
    return p


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _recompute_remaining(budget: dict[str, Any]) -> dict[str, Any]:
    caps = budget.get("caps") or {}
    usage = budget.get("usage") or {}
    today = date.today()
    ends = _parse_date(budget.get("ends_on"))
    days_left: int | None = None
    if ends is not None:
        days_left = (ends - today).days

    conf_cap = int(caps.get("max_confirmatory_class_evals", 10))
    conf_used = int(usage.get("confirmatory_class_evals", 0))
    prog_cap = int(caps.get("max_major_inefficiency_programmes", 3))
    prog_opened = int(usage.get("major_inefficiency_programmes_opened", 0))
    data_cap = int(caps.get("max_external_datasets", 2))
    data_used = int(usage.get("external_datasets_pinned", 0))

    return {
        "major_inefficiency_programmes": max(0, prog_cap - prog_opened),
        "external_datasets": max(0, data_cap - data_used),
        "confirmatory_class_evals": max(0, conf_cap - conf_used),
        "calendar_days_left": days_left,
        "ends_on": budget.get("ends_on"),
        "etf_data_deadline": budget.get("etf_data_deadline"),
    }


def _budget_lines_hit(remaining: dict[str, Any], budget: dict[str, Any]) -> list[str]:
    """Return which hard budget lines are exhausted or overdue."""
    hits: list[str] = []
    today = date.today()
    ends = _parse_date(budget.get("ends_on"))
    if ends is not None and today > ends:
        hits.append("calendar_time")
    if int(remaining.get("major_inefficiency_programmes") or 0) <= 0 and int(
        (budget.get("usage") or {}).get("major_inefficiency_programmes_opened", 0)
    ) >= int((budget.get("caps") or {}).get("max_major_inefficiency_programmes", 3)):
        # only hit if all slots opened (not "0 remaining because never started")
        opened = int((budget.get("usage") or {}).get("major_inefficiency_programmes_opened", 0))
        if opened >= int((budget.get("caps") or {}).get("max_major_inefficiency_programmes", 3)):
            hits.append("major_inefficiency_programmes")
    if int(remaining.get("confirmatory_class_evals") or 0) <= 0:
        used = int((budget.get("usage") or {}).get("confirmatory_class_evals", 0))
        cap = int((budget.get("caps") or {}).get("max_confirmatory_class_evals", 10))
        if used >= cap:
            hits.append("confirmatory_class_evals")
    if int(remaining.get("external_datasets") or 0) <= 0:
        used = int((budget.get("usage") or {}).get("external_datasets_pinned", 0))
        cap = int((budget.get("caps") or {}).get("max_external_datasets", 2))
        if used >= cap:
            hits.append("external_datasets")
    return hits


def _etf_deadline_status(budget: dict[str, Any]) -> dict[str, Any]:
    deadline = _parse_date(budget.get("etf_data_deadline"))
    today = date.today()
    queued = budget.get("queued_science") or []
    etf_blocked = any(
        q.get("id") == "etf_flow_ineff_v1" and q.get("blocked_on") for q in queued
    )
    days_to_deadline: int | None = None
    overdue = False
    if deadline is not None:
        days_to_deadline = (deadline - today).days
        overdue = today > deadline and etf_blocked
    return {
        "deadline": budget.get("etf_data_deadline"),
        "days_to_deadline": days_to_deadline,
        "still_blocked_on_etf_data": etf_blocked,
        "overdue": overdue,
        "action_if_overdue": (
            "document free-path failure and request human paid export (within dataset cap), "
            "or skip to next inefficiency, or move toward conclusion C"
            if overdue
            else None
        ),
    }


def must_conclude(budget: dict[str, Any] | None = None) -> dict[str, Any]:
    """Whether Phase 1 must issue A/B/C within the forced window."""
    b = budget if budget is not None else load_budget()
    if b.get("phase1_conclusion"):
        return {
            "must_conclude": False,
            "already_concluded": True,
            "conclusion": b.get("phase1_conclusion"),
            "reasons": [],
        }
    remaining = _recompute_remaining(b)
    hits = _budget_lines_hit(remaining, b)
    reasons = list(hits)
    etf = _etf_deadline_status(b)
    # Calendar end or any hard cap forces conclusion path
    force = bool(hits)
    return {
        "must_conclude": force,
        "already_concluded": False,
        "conclusion": None,
        "reasons": reasons,
        "forced_default": b.get(
            "forced_conclusion_if_budget_exhausted",
            "C_unlikely_robust_edge_under_constraints",
        ),
        "etf_deadline": etf,
    }


def phase1_status() -> dict[str, Any]:
    """Operator-facing Phase 1 budget + stop-rule status."""
    b = load_budget()
    remaining = _recompute_remaining(b)
    b["remaining"] = remaining
    conclude = must_conclude(b)
    etf = _etf_deadline_status(b)
    conclusion = b.get("phase1_conclusion")
    return {
        "phase": b.get("phase", "1"),
        "doc": b.get("doc", "docs/PHASE1_COMPLETION_CRITERIA.md"),
        "architecture_frozen": bool(b.get("architecture_frozen", True)),
        "started_on": b.get("started_on"),
        "ends_on": b.get("ends_on"),
        "etf_data_deadline": b.get("etf_data_deadline"),
        "active_initiative": b.get("active_initiative"),
        "suspended": b.get("suspended") or [],
        "caps": b.get("caps") or {},
        "usage": b.get("usage") or {},
        "remaining": remaining,
        "queued_science": b.get("queued_science") or [],
        "etf_deadline_status": etf,
        "must_conclude": conclude,
        "phase1_conclusion": conclusion,
        "allowed_conclusions": b.get("allowed_conclusions") or list(ALLOWED_CONCLUSIONS),
        "conclusion_labels": CONCLUSION_LABELS,
        "next_action": _next_action(b, remaining, conclude, etf),
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def _next_action(
    budget: dict[str, Any],
    remaining: dict[str, Any],
    conclude: dict[str, Any],
    etf: dict[str, Any],
) -> str:
    if budget.get("phase1_conclusion"):
        return f"Phase 1 concluded: {budget['phase1_conclusion']}. No further science under Phase 1."
    if conclude.get("must_conclude"):
        return (
            "Budget line hit or calendar ended — issue conclusion A/B/C within 7 days. "
            f"Default if quiet nulls: {conclude.get('forced_default')}."
        )
    if etf.get("overdue"):
        return (
            "ETF free-path pin overdue. Document failure + request paid export (counts as 1 dataset), "
            "skip to next inefficiency within programme budget, or move toward C."
        )
    queued = budget.get("queued_science") or []
    if queued:
        q0 = queued[0]
        blocked = q0.get("blocked_on")
        if blocked:
            return (
                f"Pin data for {q0.get('id')}: blocked_on={blocked}. "
                f"Deadline {budget.get('etf_data_deadline')}. Do not open new programmes."
            )
        return f"Execute {q0.get('id')} under frozen gates (one active programme)."
    active = (budget.get("usage") or {}).get("active_science_programme_id")
    if active:
        return f"Continue sole active science programme: {active}."
    if int(remaining.get("major_inefficiency_programmes") or 0) > 0:
        return "No queued item — open next ranked inefficiency only if budget allows; else conclude."
    return "No remaining programme slots — issue Phase 1 conclusion A/B/C."


def record_phase1_event(
    event: str,
    *,
    programme_id: str | None = None,
    result: str | None = None,
    notes: str | None = None,
    counts_as_confirmatory_class: bool = False,
    counts_as_major_programme: bool = False,
    counts_as_dataset_pin: bool = False,
    paid_spend_usd: float = 0.0,
    clear_block_on_etf: bool = False,
) -> dict[str, Any]:
    """Update Phase 1 budget counters after a science event.

    event examples: programme_opened, programme_completed, dataset_pinned,
    confirmatory_eval, free_path_failed.
    """
    b = load_budget()
    usage = dict(b.get("usage") or {})
    log = list(usage.get("programmes_log") or [])
    today = date.today().isoformat()

    entry: dict[str, Any] = {
        "event": event,
        "date": today,
    }
    if programme_id:
        entry["id"] = programme_id
    if result:
        entry["result"] = result
    if notes:
        entry["notes"] = notes
    if counts_as_confirmatory_class:
        entry["counts_as_confirmatory_class"] = True
        usage["confirmatory_class_evals"] = int(usage.get("confirmatory_class_evals", 0)) + 1
    if counts_as_major_programme and event == "programme_opened":
        usage["major_inefficiency_programmes_opened"] = (
            int(usage.get("major_inefficiency_programmes_opened", 0)) + 1
        )
        usage["active_science_programme_id"] = programme_id
    if counts_as_major_programme and event == "programme_completed":
        usage["major_inefficiency_programmes_completed"] = (
            int(usage.get("major_inefficiency_programmes_completed", 0)) + 1
        )
        if usage.get("active_science_programme_id") == programme_id:
            usage["active_science_programme_id"] = None
    if counts_as_dataset_pin:
        usage["external_datasets_pinned"] = int(usage.get("external_datasets_pinned", 0)) + 1
    if paid_spend_usd:
        usage["paid_spend_usd"] = float(usage.get("paid_spend_usd", 0)) + float(paid_spend_usd)

    log.append(entry)
    usage["programmes_log"] = log
    b["usage"] = usage

    if clear_block_on_etf or (counts_as_dataset_pin and programme_id and "etf" in programme_id.lower()):
        queued = list(b.get("queued_science") or [])
        for q in queued:
            if q.get("id") == "etf_flow_ineff_v1":
                q.pop("blocked_on", None)
                q["status"] = "ready"
        b["queued_science"] = queued

    b["remaining"] = _recompute_remaining(b)
    b["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_budget(b)
    return phase1_status()


def set_phase1_conclusion(
    conclusion: str,
    *,
    rationale: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Record the mandatory Phase 1 A/B/C conclusion.

    Rejects unknown codes. Refuses overwrite unless force=True.
    """
    if conclusion not in ALLOWED_CONCLUSIONS:
        raise ValueError(
            f"conclusion must be one of {ALLOWED_CONCLUSIONS}; got {conclusion!r}"
        )
    b = load_budget()
    existing = b.get("phase1_conclusion")
    if existing and not force:
        raise ValueError(
            f"Phase 1 already concluded as {existing!r}; pass force=True to overwrite"
        )
    b["phase1_conclusion"] = conclusion
    b["phase1_conclusion_at"] = datetime.now(timezone.utc).isoformat()
    b["phase1_conclusion_rationale"] = rationale or CONCLUSION_LABELS.get(conclusion)
    b["phase1_conclusion_label"] = CONCLUSION_LABELS.get(conclusion)
    # End active science under Phase 1
    usage = dict(b.get("usage") or {})
    usage["active_science_programme_id"] = None
    b["usage"] = usage
    b["remaining"] = _recompute_remaining(b)
    save_budget(b)
    return phase1_status()


def refuse_new_programme(reason_check: str | None = None) -> dict[str, Any]:
    """Guard: whether opening a new major programme is allowed."""
    st = phase1_status()
    if st.get("phase1_conclusion"):
        return {
            "allowed": False,
            "reason": f"Phase 1 already concluded: {st['phase1_conclusion']}",
        }
    if st.get("architecture_frozen") and reason_check == "organisational":
        return {
            "allowed": False,
            "reason": "Architecture frozen — no new organisational programmes",
        }
    active = (st.get("usage") or {}).get("active_science_programme_id")
    if active:
        return {
            "allowed": False,
            "reason": f"One active science programme only; currently {active}",
        }
    if int((st.get("remaining") or {}).get("major_inefficiency_programmes") or 0) <= 0:
        return {
            "allowed": False,
            "reason": "Major inefficiency programme budget exhausted — conclude Phase 1",
        }
    if (st.get("must_conclude") or {}).get("must_conclude"):
        return {
            "allowed": False,
            "reason": "Budget forces conclusion; do not open new programmes",
        }
    return {"allowed": True, "reason": None, "status": st}
