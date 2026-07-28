"""Living evidence-acquisition catalog and cost/EV recommendations.

Supports Workstream: maximise novel predictive information access.
Does not purchase paid APIs; only ranks and advises.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root

# Scores 1–5; cost_class: free | low | mid | high
# recommendation: free_first | acquire_free | buy_if_programme_ready | wait | reject
CATALOG: list[dict[str, Any]] = [
    {
        "id": "pm_kalshi_panel_free",
        "name": "Polymarket/Kalshi multi-market historical panel",
        "class": "prediction_markets",
        "novelty": 4,
        "pit": 3,
        "history": 4,
        "cost_class": "free",
        "cost_note": "Free public CLOB/archives; effort is assembly",
        "effort": 3,
        "ev": 4.5,
        "rank": 1,
        "recommendation": "acquire_free",
        "vs_lab": "Q2 single-binary null; panel is material redesign",
        "min_tooling": "external series attach (exists)",
        "human_required": False,
    },
    {
        "id": "vendor_exchange_flow",
        "name": "Vendor BTC(+ETH) exchange netflow (CryptoQuant/Glassnode)",
        "class": "onchain_flow",
        "novelty": 3,
        "pit": 5,
        "history": 5,
        "cost_class": "low_mid",
        "cost_note": "~USD 30–100+/mo public tiers; prefer one-time export",
        "effort": 2,
        "ev": 4.0,
        "rank": 2,
        "recommendation": "buy_if_programme_ready",
        "vs_lab": "Free CMD netflow conf-null; vendor PIT may differ",
        "min_tooling": "flow parquet drop-in (exists)",
        "human_required": True,
        "buy_when": (
            "Pre-reg programme locked AND free panel/macro path done or "
            "explicitly deprioritised AND prefer fixed export over open sub"
        ),
    },
    {
        "id": "macro_fred_dxy",
        "name": "Macro risk-off (DXY / rates via FRED-class free daily)",
        "class": "macro",
        "novelty": 3,
        "pit": 5,
        "history": 5,
        "cost_class": "free",
        "cost_note": "Public macro series (FRED/stooq-class)",
        "effort": 2,
        "ev": 3.5,
        "rank": 4,
        "recommendation": "acquire_free",
        "vs_lab": "Orthogonal to spent on-chain free filters",
        "min_tooling": "external series + small programme",
        "human_required": False,
    },
    {
        "id": "stablecoin_large_transfers",
        "name": "Large stablecoin transfer event series (academic/reconstruct)",
        "class": "onchain_events",
        "novelty": 4,
        "pit": 3,
        "history": 3,
        "cost_class": "free",
        "cost_note": "Research effort dominant",
        "effort": 4,
        "ev": 3.5,
        "rank": 3,
        "recommendation": "wait",
        "vs_lab": "Related papers exist; need reconstructible event list",
        "min_tooling": "event as-of join",
        "human_required": False,
    },
    {
        "id": "x_social_pit",
        "name": "X/Twitter sentiment PIT archive",
        "class": "social",
        "novelty": 4,
        "pit": 2,
        "history": 2,
        "cost_class": "mid_high",
        "cost_note": "API/archive cost + engineering",
        "effort": 5,
        "ev": 2.5,
        "rank": 6,
        "recommendation": "wait",
        "vs_lab": "Deferred programme; needs archive",
        "min_tooling": "high",
        "human_required": True,
    },
    {
        "id": "cmd_free_clones",
        "name": "Additional free CMD daily on-chain clones",
        "class": "onchain_misc",
        "novelty": 1,
        "pit": 2,
        "history": 4,
        "cost_class": "free",
        "cost_note": "Already used",
        "effort": 1,
        "ev": 1.0,
        "rank": 99,
        "recommendation": "reject",
        "vs_lab": "Wave Q1–Q6 nulls",
        "min_tooling": "none",
        "human_required": False,
    },
    {
        "id": "l2_orderbook",
        "name": "Crypto L2 order book history",
        "class": "microstructure",
        "novelty": 3,
        "pit": 2,
        "history": 3,
        "cost_class": "high",
        "cost_note": "Vendor / infra heavy",
        "effort": 5,
        "ev": 1.5,
        "rank": 98,
        "recommendation": "reject",
        "vs_lab": "Out of personal spot mandate scale",
        "min_tooling": "high",
        "human_required": True,
    },
]


def catalog_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "research_kb" / "evidence_acquisition_catalog.json"


def sync_catalog(root: Path | None = None) -> Path:
    root = root or project_root()
    p = catalog_path(root)
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "objective": "maximise novel predictive information access",
        "disclaimer": (
            "Public sources incomplete; costs approximate; not financial advice. "
            "Paid acquisition requires human approval."
        ),
        "buy_rule": (
            "novelty + PIT + pre-reg programme + sample adequacy + cost/EV "
            "+ drop-in integration; prefer free first; prefer export over open sub"
        ),
        "items": sorted(CATALOG, key=lambda x: float(x.get("rank") or 99)),
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2) + "\n")
    return p


def ranked_items() -> list[dict[str, Any]]:
    return sorted(CATALOG, key=lambda x: (float(x.get("rank") or 99), -float(x.get("ev") or 0)))


def recommend_spend(
    item_id: str,
    *,
    annual_usd_cost: float | None = None,
    programme_locked: bool = False,
    free_alternatives_exhausted: bool = False,
) -> dict[str, Any]:
    """Advise whether financial cost is justified for a catalog item."""
    item = next((x for x in CATALOG if x["id"] == item_id), None)
    if item is None:
        return {"ok": False, "error": f"unknown id {item_id}"}
    rec = item["recommendation"]
    reasons: list[str] = []
    buy = False

    if rec == "reject":
        reasons.append("Catalog recommendation is reject (low EV / wrong mandate)")
    elif rec == "acquire_free":
        reasons.append("Prefer free acquisition path — no purchase needed")
        buy = False
    elif rec == "buy_if_programme_ready":
        if not programme_locked:
            reasons.append("Refuse buy until programme hyps pre-registered")
        elif not free_alternatives_exhausted and item.get("id") == "vendor_exchange_flow":
            reasons.append(
                "Free multi-market / macro paths still open — try free first "
                "unless you explicitly prioritise vendor PIT"
            )
        else:
            reasons.append("Programme locked and free paths addressed or overridden")
            buy = True
        if annual_usd_cost is not None and annual_usd_cost > 600:
            reasons.append(
                f"Annual cost ${annual_usd_cost:.0f} high for personal lab — "
                "prefer one-time export / shorter commitment"
            )
            if annual_usd_cost > 2000:
                buy = False
                reasons.append("Cost exceeds informal personal research threshold")
    elif rec == "wait":
        reasons.append("Not ready — missing archive design or human keys")
    else:
        reasons.append(f"recommendation={rec}")

    return {
        "item_id": item_id,
        "recommendation_base": rec,
        "should_spend_money_now": buy,
        "reasons": reasons,
        "ev": item.get("ev"),
        "cost_note": item.get("cost_note"),
        "human_required": item.get("human_required"),
    }


def acquisition_summary() -> dict[str, Any]:
    items = ranked_items()
    return {
        "n_items": len(items),
        "top": [
            {
                "rank": i.get("rank"),
                "id": i["id"],
                "name": i["name"],
                "ev": i["ev"],
                "recommendation": i["recommendation"],
                "cost_class": i["cost_class"],
            }
            for i in items
            if i.get("recommendation") != "reject"
        ][:8],
        "reject": [i["id"] for i in items if i.get("recommendation") == "reject"],
        "next_free": next(
            (
                i["id"]
                for i in items
                if i.get("recommendation") == "acquire_free"
            ),
            None,
        ),
        "next_paid_candidate": next(
            (
                i["id"]
                for i in items
                if i.get("recommendation") == "buy_if_programme_ready"
            ),
            None,
        ),
    }
