"""Compact lab status for operators."""

from __future__ import annotations

from typing import Any

from crl.ops.doctor import run_doctor
from crl.ops.programmes import list_programmes, programmes_to_dict
from crl.production.kill_switch import is_kill_switch_engaged
from crl.production.modes import live_explicitly_enabled
from crl.production.strategies import list_approved
from crl.shared.config import load_config


def lab_status(config_path: str | None = None) -> dict[str, Any]:
    cfg = load_config(config_path)
    doctor = run_doctor(config_path)
    progs = programmes_to_dict(list_programmes())
    return {
        "doctor_ok": doctor.ok,
        "live_enabled": live_explicitly_enabled(config=cfg),
        "kill_switch": is_kill_switch_engaged(),
        "approved_strategies": list_approved(),
        "confirmatory_candidates": 0,  # none until APPROVED populated
        "programmes": {
            "n": progs["n_programmes"],
            "n_hyps": progs["n_hyps_total"],
        },
        "failed_doctor_checks": [
            c.name for c in doctor.checks if not c.ok
        ],
        "notes": [
            "Strong tool = rejection engine + paper/shadow path.",
            "No APPROVED strategies until confirmatory survivors exist.",
            *doctor.notes[:2],
        ],
    }
