"""Alpha Discovery — rank information advantages, not vendors.

Complements evidence_acquisition (vehicles) with mechanism-level ranking.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root

# Information advantages the lab may lack (not dataset shopping list)
ADVANTAGES: list[dict[str, Any]] = [
    {
        "id": "cross_event_implied_state",
        "name": "Cross-event market-implied state (prediction market panel)",
        "mechanism": (
            "Aggregated crowd probabilities across many events encode "
            "risk-on/off, policy, and path beliefs not in OHLCV alone"
        ),
        "currently_observable": "partial",
        "partial_note": "Single PM binary tested null; panel not tested",
        "reconstructible": True,
        "pit": "medium",
        "novelty_vs_lab": 5,
        "ev": 4.5,
        "cost_class": "free",
        "rank": 1,
        "action": "design_and_acquire_free_panel",
        "reject_if": "reverts to single popular binary without panel design",
    },
    {
        "id": "macro_risk_regime",
        "name": "Macro liquidity / USD regime as conditioner",
        "mechanism": "Global risk appetite and USD strength shift crypto risk premia",
        "currently_observable": "no",
        "reconstructible": True,
        "pit": "high",
        "novelty_vs_lab": 4,
        "ev": 3.5,
        "cost_class": "free",
        "rank": 2,
        "action": "acquire_free_macro_series",
        "reject_if": "used as another technical overlay without economic lag story",
    },
    {
        "id": "labeled_inventory_flow",
        "name": "Labeled exchange/ETF inventory (vendor-grade, non-revised)",
        "mechanism": "True tradable supply on venues and ETF pipes",
        "currently_observable": "partial",
        "partial_note": "Free netflow conf-null; vendor PIT may differ",
        "reconstructible": True,
        "pit": "high",
        "novelty_vs_lab": 3,
        "ev": 4.0,
        "cost_class": "paid",
        "rank": 3,
        "action": "human_export_if_programme_ready",
        "reject_if": "subscription without locked programme",
    },
    {
        "id": "event_surprise_residual",
        "name": "Price residual vs pre-event implied odds",
        "mechanism": "Under/over-reaction after resolution relative to market",
        "currently_observable": "no",
        "reconstructible": True,
        "pit": "hard",
        "novelty_vs_lab": 5,
        "ev": 3.0,
        "cost_class": "free_after_panel",
        "rank": 4,
        "action": "after_panel",
        "reject_if": "no panel history",
    },
    {
        "id": "options_skew_premium",
        "name": "Options skew / vol risk premium",
        "mechanism": "Tail insurance pricing and dealer hedging flows",
        "currently_observable": "no",
        "reconstructible": True,
        "pit": "medium",
        "novelty_vs_lab": 4,
        "ev": 2.5,
        "cost_class": "paid",
        "rank": 5,
        "action": "defer",
        "reject_if": "complexity exceeds personal mandate",
    },
    {
        "id": "social_narrative_velocity",
        "name": "Social narrative velocity with true timestamps",
        "mechanism": "Attention and herding diffusion",
        "currently_observable": "no",
        "reconstructible": "archive_dependent",
        "pit": "low_free",
        "novelty_vs_lab": 4,
        "ev": 2.0,
        "cost_class": "paid_or_blocked",
        "rank": 6,
        "action": "blocked",
        "reject_if": "unversioned scrape",
    },
    {
        "id": "l2_imbalance",
        "name": "L2 order-book imbalance",
        "mechanism": "Short-horizon informed trading",
        "currently_observable": "no",
        "reconstructible": True,
        "pit": "hard",
        "novelty_vs_lab": 3,
        "ev": 1.0,
        "cost_class": "high",
        "rank": 99,
        "action": "reject",
        "reject_if": "always for this capital/horizon mandate",
    },
    {
        "id": "free_onchain_metric_clone",
        "name": "Another free daily on-chain metric (same family)",
        "mechanism": "Redundant inventory/activity proxies",
        "currently_observable": "yes_exhausted",
        "reconstructible": True,
        "pit": "weak",
        "novelty_vs_lab": 1,
        "ev": 0.5,
        "cost_class": "free",
        "rank": 100,
        "action": "reject",
        "reject_if": "always after Q1–Q6 null wave",
    },
]


def catalog_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "research_kb" / "alpha_discovery_catalog.json"


def sync_catalog(root: Path | None = None) -> Path:
    root = root or project_root()
    p = catalog_path(root)
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "directive": "docs/ALPHA_DISCOVERY_DIRECTIVE.md",
        "question": (
            "What information advantage might exist that this laboratory "
            "cannot currently observe?"
        ),
        "advantages": sorted(ADVANTAGES, key=lambda x: float(x.get("rank") or 99)),
        "self_critique_seed": (
            "World-class group would prioritise missing information and "
            "multiplicity discipline over more engineering — hypothesis only."
        ),
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2) + "\n")
    return p


def ranked_advantages() -> list[dict[str, Any]]:
    return sorted(ADVANTAGES, key=lambda x: (float(x.get("rank") or 99), -float(x.get("ev") or 0)))


def discovery_summary() -> dict[str, Any]:
    active = [a for a in ranked_advantages() if a.get("action") not in ("reject",)]
    return {
        "n_advantages": len(ADVANTAGES),
        "top_actionable": [
            {
                "rank": a["rank"],
                "id": a["id"],
                "name": a["name"],
                "ev": a["ev"],
                "action": a["action"],
                "cost_class": a["cost_class"],
                "currently_observable": a["currently_observable"],
            }
            for a in active
            if a.get("action") not in ("defer", "blocked", "after_panel")
        ][:5],
        "next": next(
            (a["id"] for a in ranked_advantages() if a.get("action") not in ("reject", "defer", "blocked")),
            None,
        ),
        "rejected": [a["id"] for a in ADVANTAGES if a.get("action") == "reject"],
        "success_metric": "P(robust predictive information under frozen gates)",
    }


def self_critique_prompt() -> dict[str, Any]:
    return {
        "question": (
            "If a world-class quantitative research organisation started this "
            "laboratory today, what would they improve first?"
        ),
        "current_hypotheses": [
            "Missing information classes, not missing code",
            "Multiplicity discipline already improving (family ledger)",
            "Free clone mining is negative EV",
            "Paid data only with pre-reg and free alternatives considered",
        ],
        "status": "hypotheses_not_facts",
    }
