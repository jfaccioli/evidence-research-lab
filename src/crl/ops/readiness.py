"""Lab vs live readiness scores — honest dual metric."""

from __future__ import annotations

from typing import Any

from crl.ops.doctor import run_doctor
from crl.ops.programmes import list_programmes
from crl.ops.status import lab_status
from crl.production.paper.clock import default_clock_dir, paper_clock_satisfied
from crl.production.strategies import list_approved
from crl.shared.config import project_root


def readiness_report(config_path: str | None = None) -> dict[str, Any]:
    """Return lab_ops readiness (high) vs autotrading readiness (low until survivors)."""
    st = lab_status(config_path)
    doctor = run_doctor(config_path)
    progs = list_programmes()
    root = project_root()

    lab_checks = {
        "doctor_ok": st["doctor_ok"],
        "git_origin": any(
            c.name == "git_origin" and c.ok for c in doctor.checks
        ),
        "live_disabled": not st["live_enabled"],
        "kill_switch_clear": not st["kill_switch"],
        "programmes_present": len(progs) > 0,
        "paper_shadow_imports": any(
            c.name == "production_imports" and c.ok for c in doctor.checks
        ),
        "no_leverage_mandate": True,
        "flow_scaffold_present": (root / "src/crl/shared/data/flow.py").exists()
        and (root / "examples/batch/flow").is_dir(),
    }
    lab_score = sum(1 for v in lab_checks.values() if v) / max(len(lab_checks), 1)

    n_approved = len(list_approved())
    clock = paper_clock_satisfied(default_clock_dir(root), min_survivors=2)
    # Shadow reconciliation remains a formal record (not auto-true)
    shadow_marker = root / "data" / "shadow" / "RECONCILED.json"
    shadow_ok = shadow_marker.exists()
    trade_checks = {
        "confirmatory_survivors_ge_2": n_approved >= 2,
        "approved_registry_populated": n_approved > 0,
        "paper_clock_on_survivors": bool(clock["ok"]),
        "shadow_reconciled": shadow_ok,
        "phase5_human_open": st["live_enabled"],  # should be False until human opens
    }
    # Autotrading "ready" requires survivors + paper + shadow; phase5 open is last step
    trade_ready_core = (
        trade_checks["confirmatory_survivors_ge_2"]
        and trade_checks["paper_clock_on_survivors"]
        and trade_checks["shadow_reconciled"]
    )
    # Never report autotrading_ready True solely from partial path
    autotrading_ready = trade_ready_core and st["live_enabled"]
    trade_score = (
        (1.0 if trade_checks["confirmatory_survivors_ge_2"] else 0.0)
        + (1.0 if trade_checks["paper_clock_on_survivors"] else 0.0)
        + (1.0 if trade_checks["shadow_reconciled"] else 0.0)
    ) / 3.0

    return {
        "lab_ops_ready": lab_score >= 0.99 and st["doctor_ok"],
        "lab_ops_score": round(lab_score, 3),
        "lab_ops_checks": lab_checks,
        "autotrading_ready": autotrading_ready,
        "autotrading_score": round(trade_score, 3),
        "autotrading_checks": trade_checks,
        "paper_clock_detail": {
            "ok": clock["ok"],
            "reason": clock["reason"],
            "complete": clock["complete"],
            "incomplete": clock["incomplete"],
        },
        "autotrading_ready_if": [
            "≥2 independent confirmatory survivors in APPROVED",
            "paper clock completed on those survivors (data/paper_clock/)",
            "shadow reconciled on live feed (data/shadow/RECONCILED.json)",
            "human Phase-5 open + keys + no leverage",
        ],
        "close_to_tiny_live": trade_ready_core and not st["live_enabled"],
        "message": (
            "Lab ops mature; autotrading not ready (0 confirmatory survivors)."
            if n_approved == 0
            else (
                "CLOSE TO TINY LIVE — human Phase-5 open still required."
                if trade_ready_core and not st["live_enabled"]
                else "Survivors present — continue paper/shadow ladder."
            )
        ),
    }
