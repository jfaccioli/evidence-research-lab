"""Deployment and rollback procedures (documented + machine checklist).

No automatic LIVE. Scientific APPROVED registry remains the only path for
alpha strategies. Benchmarks may only deploy to paper validation.
"""

from __future__ import annotations

from typing import Any

from crl.platform.strategy import StrategyMeta
from crl.production.modes import live_explicitly_enabled
from crl.production.strategies.registry import is_approved


DEPLOYMENT_CHECKLIST: list[str] = [
    "strategy_id registered in platform",
    "if alpha: id in production.strategies.APPROVED (confirmatory path)",
    "if benchmark: paper/shadow only — never LIVE",
    "ops-readiness checklist green",
    "kill switch clear",
    "risk envelope max_leverage=1",
    "audit logging path writable",
    "rollback: pin previous strategy_id + config hash",
]


def deployment_gate(meta: StrategyMeta) -> dict[str, Any]:
    """Return whether a strategy may enter paper validation or is blocked."""
    live = live_explicitly_enabled()
    if meta.is_benchmark:
        return {
            "strategy_id": meta.id,
            "allow_paper": True,
            "allow_shadow": True,
            "allow_live": False,
            "reason": "benchmark engineering artefact — LIVE permanently disabled",
            "checklist": DEPLOYMENT_CHECKLIST,
        }
    approved = is_approved(meta.id)
    return {
        "strategy_id": meta.id,
        "allow_paper": approved,
        "allow_shadow": approved,
        "allow_live": False,  # always dual-flag + human; never auto
        "live_flags_present": live,
        "reason": (
            "scientific candidate requires APPROVED registry for paper/shadow; "
            "LIVE always requires dual human flags and remains stubbed"
            if not approved
            else "approved for paper/shadow only; LIVE still dual-flag stub"
        ),
        "checklist": DEPLOYMENT_CHECKLIST,
    }


def rollback_plan(current_id: str, previous_id: str) -> dict[str, str]:
    return {
        "action": "rollback",
        "from": current_id,
        "to": previous_id,
        "steps": (
            "1. Engage kill switch. "
            "2. Stop paper/shadow workers. "
            "3. Restore previous strategy_id and config hash in run config. "
            "4. Clear kill switch only after audit. "
            "5. Do not open LIVE without re-validation."
        ),
    }
