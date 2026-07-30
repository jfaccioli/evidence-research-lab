"""Economic Inefficiency Programme — rank plausible temporary predictabilities."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root


def catalogue_path() -> Path:
    return project_root() / "research_kb" / "rd" / "inefficiency_catalogue.json"


def load_catalogue() -> dict[str, Any]:
    p = catalogue_path()
    if not p.exists():
        return {"version": 0, "inefficiencies": []}
    return json.loads(p.read_text())


def iscore(
    *,
    Dur: float,
    EV: float,
    Obs: float,
    DataCost: float,
    Pa: float,
    Overlap: float,
) -> float:
    return round(
        1.4 * Dur + 1.3 * EV + 1.2 * Obs + 1.0 * DataCost + 1.6 * Pa - 1.3 * Overlap,
        4,
    )


def ranked_inefficiencies() -> list[dict[str, Any]]:
    cat = load_catalogue()
    rows = []
    for item in cat.get("inefficiencies") or []:
        s = item.get("scores") or {}
        score = iscore(
            Dur=float(s.get("Dur", 0)),
            EV=float(s.get("EV", 0)),
            Obs=float(s.get("Obs", 0)),
            DataCost=float(s.get("DataCost", 0)),
            Pa=float(s.get("Pa", 0)),
            Overlap=float(s.get("Overlap", 0)),
        )
        row = dict(item)
        row["IScore"] = score
        rows.append(row)
    rows.sort(key=lambda r: (-r["IScore"], r.get("rank", 99)))
    return rows


def top_inefficiency() -> dict[str, Any] | None:
    rows = ranked_inefficiencies()
    return rows[0] if rows else None


def eir_required(top: dict[str, Any] | None = None) -> bool:
    t = top or top_inefficiency()
    if not t:
        return False
    if t.get("lab_has_observables") is True:
        return False
    if t.get("lab_has_observables") == "partial" and t.get("status") in (
        "data_gap",
        "eir_required",
    ):
        return True
    if t.get("lab_has_observables") is False:
        return True
    return t.get("status") in ("eir_required", "data_gap")


def inefficiency_report() -> dict[str, Any]:
    rows = ranked_inefficiencies()
    top = rows[0] if rows else None
    need_eir = eir_required(top)
    return {
        "programme": "ECONOMIC_INEFFICIENCY_PROGRAMME_V1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "objective": (
            "Identify economically plausible reasons BTC might be temporarily "
            "predictable; find smallest extra information for the best remaining inefficiency"
        ),
        "suspended": "immediate_deployable_strategy_search_from_free_shelf",
        "n_inefficiencies": len(rows),
        "ranked": [
            {
                "rank": i + 1,
                "id": r["id"],
                "name": r["name"],
                "IScore": r["IScore"],
                "status": r.get("status"),
                "lab_has_observables": r.get("lab_has_observables"),
                "min_additional_data": r.get("min_additional_data"),
                "scores": r.get("scores"),
            }
            for i, r in enumerate(rows)
        ],
        "top": {
            "id": top["id"] if top else None,
            "name": top["name"] if top else None,
            "IScore": top["IScore"] if top else None,
            "why_exists": top.get("why_exists") if top else None,
            "who_creates": top.get("who_creates") if top else None,
            "why_not_arbed_immediately": top.get("why_not_arbed_immediately") if top else None,
            "observables": top.get("observables") if top else None,
            "lab_has_observables": top.get("lab_has_observables") if top else None,
            "min_additional_data": top.get("min_additional_data") if top else None,
        }
        if top
        else None,
        "eir_required": need_eir,
        "eir_path": (
            "docs/EVIDENCE_INVESTMENT_REVIEW_INEFFICIENCY_2026-07-30.md"
            if need_eir
            else None
        ),
        "recommendation": (
            "Acquire free delayed US spot BTC ETF net flow series with PIT lag; "
            "do not pay for vendor API until free path fails; do not re-mine free shelf strategies"
            if need_eir
            else "Investigate top inefficiency with existing data"
        ),
        "standards": {
            "gates_frozen": True,
            "not_dataset_first": True,
            "platform_is_not_alpha": True,
        },
    }
