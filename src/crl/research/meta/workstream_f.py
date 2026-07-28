"""Workstream F — scientific meta-research principles ledger.

Principles are drawn from *public* literature and process descriptions.
They are not a claim of proprietary fund methods.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root

# status: maintain | implement | scheduled | defer | reject
PRINCIPLES: list[dict[str, Any]] = [
    {
        "id": "P1_preregister",
        "name": "Pre-register hypotheses before evaluation outcomes",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "none",
        "notes": "Programme INDEX + hyp YAMLs",
    },
    {
        "id": "P2_holdout_confirmatory",
        "name": "Exploratory vs confirmatory holdout; frozen primary metric",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "none",
        "notes": "configs/default.yaml gates + ResearchMode",
    },
    {
        "id": "P3_trial_family_ledger",
        "name": "Count trials/families for multiplicity awareness",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "low",
        "notes": "family_trial_ledger.json; auto-update on run-programme (F1)",
    },
    {
        "id": "P4_deflated_sharpe",
        "name": "Selection-aware / deflated Sharpe awareness",
        "lab": "partial",
        "status": "scheduled",
        "sci_ev": "med_high",
        "effort": "med",
        "notes": "promotion module mentions DSR; auto annotation = F2",
    },
    {
        "id": "P5_no_test_tuning",
        "name": "No tuning on confirmatory test; one-shot conf",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "none",
    },
    {
        "id": "P6_pit_data",
        "name": "Point-in-time data joins",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "none",
    },
    {
        "id": "P7_research_prioritisation",
        "name": "Explicit research prioritisation / queue",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "low",
        "notes": "RESEARCH_QUEUE.md + research_queue_state.json",
    },
    {
        "id": "P8_retire_exhausted",
        "name": "Retire exhausted families",
        "lab": "partial",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "low",
        "notes": "thesis tree + Phase2 closeout",
    },
    {
        "id": "P9_alpha_lifecycle",
        "name": "Paper → shadow → live lifecycle",
        "lab": "scaffolded",
        "status": "defer",
        "sci_ev": "med",
        "effort": "med",
        "notes": "Blocked on APPROVED survivors",
    },
    {
        "id": "P10_live_drift_monitor",
        "name": "Live drift / strategy monitoring",
        "lab": "absent",
        "status": "defer",
        "sci_ev": "low",
        "effort": "high",
        "notes": "No live strategies",
    },
    {
        "id": "P11_portfolio_construction",
        "name": "Multi-strategy portfolio construction",
        "lab": "absent",
        "status": "reject",
        "sci_ev": "low",
        "effort": "high",
        "notes": "Premature with 0 survivors",
    },
    {
        "id": "P12_nn_hypothesis",
        "name": "NN/RL as primary hypothesis class",
        "lab": "out_of_mandate",
        "status": "reject",
        "sci_ev": "n/a",
        "effort": "n/a",
    },
    {
        "id": "P13_pbo_cscv",
        "name": "Full PBO/CSCV on every programme",
        "lab": "absent",
        "status": "defer",
        "sci_ev": "med",
        "effort": "high",
        "notes": "Strict gates already; revisit if trial counts explode",
    },
    {
        "id": "P14_reality_checks",
        "name": "Economic reality / fee fragility checks",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "none",
    },
    {
        "id": "P15_fail_closed_promotion",
        "name": "Fail-closed promotion path",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "none",
    },
    {
        "id": "P16_meta_research_ws",
        "name": "Permanent scientific meta-research workstream",
        "lab": "implemented",
        "status": "maintain",
        "sci_ev": "high",
        "effort": "low",
        "notes": "This module + WORKSTREAM_F doc",
    },
]


def principles_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "research_kb" / "meta_research_principles.json"


def sync_principles_file(root: Path | None = None) -> Path:
    root = root or project_root()
    p = principles_path(root)
    payload = {
        "version": 1,
        "workstream": "F",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Public process literature only; not proprietary fund methods. "
            "Incomplete evidence."
        ),
        "principles": PRINCIPLES,
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2) + "\n")
    return p


def principles_report() -> dict[str, Any]:
    by_status: dict[str, list[str]] = {}
    for pr in PRINCIPLES:
        by_status.setdefault(pr["status"], []).append(pr["id"])
    return {
        "n_principles": len(PRINCIPLES),
        "by_status": {k: len(v) for k, v in by_status.items()},
        "implement_now": [p for p in PRINCIPLES if p["status"] == "implement"],
        "scheduled": [p for p in PRINCIPLES if p["status"] == "scheduled"],
        "deferred": [p["id"] for p in PRINCIPLES if p["status"] == "defer"],
        "rejected": [p["id"] for p in PRINCIPLES if p["status"] == "reject"],
    }
