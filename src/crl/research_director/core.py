"""Research Director core: programme map, ranking, knowledge graph, reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crl.shared.config import project_root


def rd_root() -> Path:
    return project_root() / "research_kb" / "rd"


def _load_json(name: str) -> dict[str, Any]:
    path = rd_root() / name
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_json(name: str, obj: dict[str, Any]) -> Path:
    path = rd_root() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")
    return path


def list_programmes() -> list[dict[str, Any]]:
    return list(_load_json("programmes.json").get("programmes") or [])


def list_areas() -> list[dict[str, Any]]:
    return list(_load_json("research_areas.json").get("areas") or [])


def composite_score(
    *,
    EIG: float,
    EEV: float,
    Pa: float,
    SciRisk: float,
    EngCost: float,
    ExtDep: float,
    Overlap: float,
) -> float:
    """Joint priority score (higher = more attractive)."""
    return round(
        1.5 * EIG
        + 1.2 * EEV
        + 1.5 * Pa
        - 0.8 * SciRisk
        - 0.7 * EngCost
        - 0.5 * ExtDep
        - 1.2 * Overlap,
        4,
    )


def ranked_directions(
    *,
    include_forbidden: bool = False,
) -> list[dict[str, Any]]:
    raw = _load_json("directions.json")
    dirs = list(raw.get("directions") or [])
    out = []
    for d in dirs:
        if not include_forbidden and d.get("status") in ("forbidden",):
            continue
        score = composite_score(
            EIG=float(d.get("EIG", 0)),
            EEV=float(d.get("EEV", 0)),
            Pa=float(d.get("Pa", 0)),
            SciRisk=float(d.get("SciRisk", 0)),
            EngCost=float(d.get("EngCost", 0)),
            ExtDep=float(d.get("ExtDep", 0)),
            Overlap=float(d.get("Overlap", 0)),
        )
        row = dict(d)
        row["composite_score"] = score
        out.append(row)
    out.sort(key=lambda r: (-r["composite_score"], r.get("id", "")))
    return out


def knowledge_graph_summary() -> dict[str, Any]:
    g = _load_json("knowledge_graph.json")
    nodes = g.get("nodes") or []
    edges = g.get("edges") or []
    by_layer: dict[str, int] = {}
    for n in nodes:
        layer = n.get("layer", "unknown")
        by_layer[layer] = by_layer.get(layer, 0) + 1
    by_status: dict[str, int] = {}
    for e in edges:
        st = e.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1
    refuted = [e for e in edges if "refut" in str(e.get("status", ""))]
    supported = [
        e
        for e in edges
        if str(e.get("status", "")).startswith("supported")
    ]
    return {
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "nodes_by_layer": by_layer,
        "edges_by_status": by_status,
        "n_supported_edges": len(supported),
        "n_refuted_or_retired_edges": len(refuted)
        + sum(1 for e in edges if e.get("status") in ("retired", "null", "refuted_incremental")),
        "layers": g.get("layers"),
    }


def load_retired_families() -> list[str]:
    """Merge RD directions + mechanism registry retirements."""
    retired: set[str] = set()
    mech_path = project_root() / "research_kb" / "mechanism_registry.json"
    if mech_path.exists():
        reg = json.loads(mech_path.read_text())
        for f in reg.get("retired_combination_families") or []:
            retired.add(str(f))
    for d in _load_json("directions.json").get("directions") or []:
        if d.get("status") == "forbidden":
            retired.add(str(d.get("id")))
        for o in d.get("retired_overlap") or []:
            retired.add(str(o))
    return sorted(retired)


def is_duplicate_or_retired(keyword: str) -> dict[str, Any]:
    """Check whether a proposed topic collides with retired work."""
    kw = keyword.lower()
    tokens = {t for t in kw.replace("/", " ").replace("-", " ").split() if len(t) > 2}
    hits = []
    for r in load_retired_families():
        rl = r.lower()
        if kw in rl or rl in kw or any(t in rl for t in tokens):
            hits.append(r)
    for a in list_areas():
        blob = " ".join(
            [
                a.get("id", ""),
                a.get("name", ""),
                a.get("notes", ""),
                " ".join(a.get("retirement_registry") or []),
                a.get("hypothesis_registry") or "",
            ]
        ).lower()
        for r in a.get("retirement_registry") or []:
            if kw in str(r).lower() or any(t in str(r).lower() for t in tokens):
                hits.append(f"area:{a['id']}:{r}")
        if a.get("status") in (
            "exhausted_public_atomistic",
            "mostly_null",
            "null_atomistic",
        ):
            area_tokens = set(a["id"].replace("_", " ").split()) | set(
                a.get("name", "").lower().split()
            )
            if tokens & area_tokens or any(t in blob for t in tokens if t in area_tokens):
                hits.append(f"area_status:{a['id']}:{a['status']}")
            # explicit high-overlap tokens for exhausted areas
            if a["id"] == "trend_momentum" and tokens & {
                "mom",
                "momentum",
                "trend",
                "tsmom",
                "sma",
            }:
                hits.append(f"area_status:{a['id']}:{a['status']}")
    # de-dupe preserve order
    seen: set[str] = set()
    uniq = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return {
        "query": keyword,
        "blocked": len(uniq) > 0,
        "hits": uniq[:20],
        "note": "If blocked, do not open programme without new data class + pre-reg",
    }


def annual_objective() -> str:
    return (
        "Increase the laboratory's understanding of how markets function while "
        "maximising the probability of discovering economically meaningful, "
        "reproducible trading advantages under frozen scientific standards."
    )


def director_report() -> dict[str, Any]:
    """Full RD snapshot for humans and autonomous agents."""
    ranked = ranked_directions(include_forbidden=False)
    openable = [
        d
        for d in ranked
        if d.get("status")
        not in ("forbidden", "policy_done", "deferred_eir", "blocked_missing_free_series")
    ]
    blocked = [
        d
        for d in ranked
        if d.get("status")
        in ("blocked_missing_free_series", "deferred_eir", "forbidden")
    ]
    top = ranked[0] if ranked else None
    try:
        from crl.research_director.inefficiency import inefficiency_report

        ineff = inefficiency_report()
    except Exception as exc:  # pragma: no cover
        ineff = {"error": str(exc)}
    return {
        "programme": "research_director",
        "role": "principal_investigator",
        "annual_objective": annual_objective(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "active_initiative": "ECONOMIC_INEFFICIENCY_PROGRAMME_V1",
        "suspended": "immediate_deployable_strategy_search_from_free_shelf",
        "programmes": list_programmes(),
        "n_research_areas": len(list_areas()),
        "areas": [
            {
                "id": a["id"],
                "name": a["name"],
                "status": a["status"],
                "notes": a.get("notes"),
            }
            for a in list_areas()
        ],
        "knowledge_graph": knowledge_graph_summary(),
        "ranked_directions": ranked,
        "economic_inefficiency": ineff,
        "top_openable_direction": next(
            (
                d
                for d in ranked
                if d.get("status")
                in (
                    "evaluate_free_source",
                    "optional_low_priority",
                    "active_engineering",
                )
            ),
            top,
        ),
        "blocked_high_value": [
            d
            for d in ranked
            if d.get("status") in ("blocked_missing_free_series", "deferred_eir")
        ][:5],
        "retired_family_count": len(load_retired_families()),
        "allocation_guidance": {
            "alpha_discovery": "Execute only RD-opened inefficiency programmes under frozen gates",
            "economic_inefficiency": "Primary science initiative — market economics first",
            "mechanism_discovery": "Subordinate to inefficiency catalogue",
            "trading_platform": "Engineering only; no science budget from alpha",
            "ops_governance": "Maintain; do not expand for novelty",
        },
        "current_scientific_model": (
            "Next-RV dominated by RV lag; free-shelf deployable strategies null under PCS; "
            "most plausible remaining temporary predictability is structural ETF create/redeem "
            "flow — requires data not on free OHLCV shelf; 0 confirmatory trading candidates"
        ),
        "standards": {
            "gates": "frozen",
            "trading_platform_is_alpha": False,
            "weaken_gates_for_platform": False,
        },
        "interrupt_policy": [
            "new high-value programme open",
            "external data scientifically justified (EIR)",
            "confirmatory survivor",
            "major model contradiction",
            "strategic human judgement required",
        ],
        "openable_count": len(openable),
        "blocked_count": len(blocked),
    }


def sync_rd_state() -> dict[str, Any]:
    """Refresh derived state file for agents and humans."""
    report = director_report()
    path = _save_json("director_state.json", report)
    # Human-readable short report
    md_path = project_root() / "research_kb" / "RD_STATUS.md"
    lines = [
        "# Research Director Status",
        "",
        f"**Updated:** {report['updated_at']}",
        "",
        f"**Objective:** {report['annual_objective']}",
        "",
        "## Current model",
        "",
        report["current_scientific_model"],
        "",
        "## Programmes",
        "",
    ]
    for p in report["programmes"]:
        lines.append(f"- **{p['name']}** (`{p['id']}`): {p['status']} — {p['role']}")
    lines.extend(["", "## Ranked directions (open-ish)", ""])
    for d in report["ranked_directions"][:8]:
        lines.append(
            f"- **{d['composite_score']:.2f}** `{d['id']}` — {d['title']} "
            f"[{d['status']}]"
        )
    lines.extend(["", "## Knowledge graph", ""])
    kg = report["knowledge_graph"]
    lines.append(
        f"Nodes: {kg['n_nodes']} · Edges: {kg['n_edges']} · "
        f"Supported: {kg['n_supported_edges']} · Refuted/retired-ish: {kg['n_refuted_or_retired_edges']}"
    )
    lines.extend(["", "## Standards", "", "- Gates frozen", "- Platform ≠ alpha", ""])
    md_path.write_text("\n".join(lines) + "\n")
    return {"state_path": str(path), "md_path": str(md_path), "report": report}
