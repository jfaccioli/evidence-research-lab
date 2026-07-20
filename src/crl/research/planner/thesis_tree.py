"""Research Thesis Tree — track economic mechanisms and uncertainty reduction.

Not a trading module. Confidence is epistemic (how sure we are about the claim),
not expected profit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from crl.research.planner.analyze import RegistryAnalysis, analyze_registry
from crl.research.planner.mechanisms import MECHANISMS, MECH_BY_ID, infer_mechanisms

Stance = Literal[
    "untested",
    "active",
    "weakly_supported",
    "nominated_confirmatory",  # evidence lean positive — still must pass gates
    "refuted",
    "retired",
    "exhausted_null",
]


@dataclass
class ThesisNode:
    mechanism_id: str
    name: str
    claim: str
    stance: Stance
    confidence: float  # 0–1 epistemic confidence in the *stance* (not in alpha)
    n_tests: int
    n_passed_val: int
    n_failed_test: int
    n_candidate: int
    supporting: list[str] = field(default_factory=list)
    refuting: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    recommendation: str = "observe"  # observe | nominate_confirmatory | pivot | retire
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanism_id": self.mechanism_id,
            "name": self.name,
            "claim": self.claim,
            "stance": self.stance,
            "confidence": round(self.confidence, 3),
            "n_tests": self.n_tests,
            "n_passed_val": self.n_passed_val,
            "n_failed_test": self.n_failed_test,
            "n_candidate": self.n_candidate,
            "supporting": self.supporting,
            "refuting": self.refuting,
            "unknowns": self.unknowns,
            "recommendation": self.recommendation,
            "last_updated": self.last_updated,
        }


@dataclass
class ThesisTree:
    updated_at: str
    nodes: list[ThesisNode]
    global_unknowns: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "updated_at": self.updated_at,
            "summary": self.summary,
            "global_unknowns": self.global_unknowns,
            "nodes": [n.to_dict() for n in self.nodes],
        }


def thesis_paths(root: Path) -> dict[str, Path]:
    base = root / "research_kb"
    return {
        "json": base / "thesis_tree.json",
        "md": base / "THESIS_TREE.md",
    }


def rebuild_thesis_tree(
    registry_path: Path,
    root: Path,
    *,
    experiment_notes: list[dict[str, Any]] | None = None,
) -> ThesisTree:
    """Rebuild tree from registry evidence + optional per-experiment notes."""
    analysis = analyze_registry(registry_path)
    notes_by_mech: dict[str, list[dict[str, Any]]] = {}
    for en in experiment_notes or []:
        for mid in en.get("mechanism_ids") or []:
            notes_by_mech.setdefault(mid, []).append(en)

    # Aggregate hyp outcomes per mechanism from registry
    mech_stats = _mechanism_stats_from_registry(registry_path)

    now = datetime.now(timezone.utc).isoformat()
    nodes: list[ThesisNode] = []
    for m in MECHANISMS:
        st = mech_stats.get(
            m.id,
            {"n": 0, "passed_val": 0, "failed_test": 0, "candidate": 0, "failed": 0},
        )
        node = _infer_node(m.id, m.name, m.description, st, analysis, notes_by_mech.get(m.id, []))
        node.last_updated = now
        nodes.append(node)

    # Sort: active/weakly_supported first, then untested, then retired/refuted
    order = {
        "nominated_confirmatory": 0,
        "weakly_supported": 1,
        "active": 2,
        "untested": 3,
        "exhausted_null": 4,
        "refuted": 5,
        "retired": 6,
    }
    nodes.sort(key=lambda n: (order.get(n.stance, 9), -n.n_tests, n.mechanism_id))

    global_unknowns = [
        "No confirmatory *candidates* yet — uncertainty remains high on all mechanisms.",
        "Daily BTC long-only space may be saturated with public technical rules.",
        "True funding/OI/on-chain PIT series not yet in evidence base.",
        "Whether *any* low-frequency BTC spot edge survives costs + multiple testing is open.",
    ]
    if any(n.stance == "nominated_confirmatory" for n in nodes):
        global_unknowns.insert(
            0,
            "At least one mechanism nominated for confirmatory — gates still decide.",
        )

    n_ref = sum(1 for n in nodes if n.stance in ("refuted", "retired", "exhausted_null"))
    n_open = sum(1 for n in nodes if n.stance in ("untested", "active", "weakly_supported"))
    summary = (
        f"{len(nodes)} mechanisms tracked; {n_ref} closed/retired/null; "
        f"{n_open} still open; "
        f"registry n={analysis.n_hypotheses}. "
        "Success = uncertainty reduction, not alpha discovery."
    )

    tree = ThesisTree(
        updated_at=now,
        nodes=nodes,
        global_unknowns=global_unknowns,
        summary=summary,
    )
    _write_tree(root, tree)
    return tree


def _mechanism_stats_from_registry(registry_path: Path) -> dict[str, dict[str, int]]:
    import sqlite3

    path = Path(registry_path)
    out: dict[str, dict[str, int]] = {
        m.id: {"n": 0, "passed_val": 0, "failed_test": 0, "candidate": 0, "failed": 0}
        for m in MECHANISMS
    }
    if not path.exists():
        return out
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT id, status, rationale, taxonomy, spec_json FROM hypotheses").fetchall()
    finally:
        conn.close()

    for r in rows:
        blob = f"{r['id']} {r['rationale'] or ''} {r['taxonomy'] or ''} {r['spec_json'] or ''}"
        mechs = [
            m
            for m in infer_mechanisms(blob, taxonomy=r["taxonomy"] or "")
            if m != "unknown"
        ]
        st = r["status"] or ""
        for mid in mechs:
            if mid not in out:
                out[mid] = {"n": 0, "passed_val": 0, "failed_test": 0, "candidate": 0, "failed": 0}
            out[mid]["n"] += 1
            if st == "passed_val":
                out[mid]["passed_val"] += 1
            elif st == "failed_test":
                out[mid]["failed_test"] += 1
            elif st == "candidate":
                out[mid]["candidate"] += 1
            elif st.startswith("failed") or st == "rejected":
                out[mid]["failed"] += 1
    return out


def _infer_node(
    mid: str,
    name: str,
    claim: str,
    st: dict[str, int],
    analysis: RegistryAnalysis,
    exp_notes: list[dict[str, Any]],
) -> ThesisNode:
    n = st["n"]
    pv = st["passed_val"]
    ft = st["failed_test"]
    cand = st["candidate"]
    failed = st["failed"]

    supporting: list[str] = []
    refuting: list[str] = []
    unknowns: list[str] = [
        "OOS confirmatory not earned or not run.",
        "Multiple-testing burden grows with family size.",
    ]

    for en in exp_notes:
        if en.get("supports"):
            supporting.append(str(en["supports"]))
        if en.get("refutes"):
            refuting.append(str(en["refutes"]))
        if en.get("unknown"):
            unknowns.append(str(en["unknown"]))

    # Default epistemic inference from counts
    if n == 0:
        stance: Stance = "untested"
        conf = 0.1
        rec = "observe"
        unknowns.append("No direct tests yet — high IG if economically distinct.")
    elif cand > 0:
        stance = "nominated_confirmatory"
        conf = 0.55
        rec = "nominate_confirmatory"
        supporting.append(f"{cand} registry candidate status (gates already applied).")
    elif pv > 0 and ft > 0:
        stance = "exhausted_null"
        conf = 0.65
        rec = "retire"
        refuting.append(
            f"Exploratory pass then confirmatory fail (pv={pv}, failed_test={ft}) — "
            "do not trust val-only signals."
        )
        supporting.append("Process worked: false discovery caught.")
    elif pv > 0 and ft == 0 and cand == 0:
        stance = "weakly_supported"
        conf = 0.35
        rec = "nominate_confirmatory"
        supporting.append(
            f"{pv} exploratory passed_val — **nominate** confirmatory; gates still decide."
        )
        unknowns.append("Val pass may be selection artifact until confirmatory.")
    elif n >= 12 and failed >= n - 1 and pv == 0 and ft == 0:
        stance = "exhausted_null"
        conf = 0.7
        rec = "retire"
        refuting.append(f"Large null body (n≈{n}) with no exploratory survival.")
    elif n >= 6 and failed == n and pv == 0 and ft == 0:
        stance = "refuted"
        conf = 0.5
        rec = "pivot"
        refuting.append(f"All {n} tests failed exploratory/gates under current design class.")
        unknowns.append("A structurally different operationalisation might still be open.")
    elif n <= 2 and failed >= 1 and pv == 0:
        stance = "active"
        conf = 0.35
        rec = "pivot"
        refuting.append("Early failure(s) — formulation-specific; mechanism not fully closed.")
        for en in exp_notes:
            if en.get("refutes"):
                conf = 0.45
    elif n >= 3 and failed > pv and pv == 0:
        stance = "active"
        conf = 0.4
        rec = "pivot"
        refuting.append(f"Failures dominate (failed≈{failed}, n={n}); no exploratory survival yet.")
        unknowns.append("May still be open under a different operationalisation.")
    else:
        stance = "active"
        conf = 0.3 + min(0.3, n * 0.03)
        rec = "observe"
        if failed > pv:
            refuting.append(f"More failures ({failed}) than exploratory passes ({pv}).")

    # Coverage from analysis underrepresented
    if mid in analysis.underrepresented_mechanisms and n <= 2:
        unknowns.append("Underrepresented in catalog — remaining uncertainty high.")

    # Specific known high-value nulls
    if mid == "asymmetric_capture" and n >= 1:
        refuting.append(
            "plan_asymmetric_capture_vol_gate: val excess vs B&H strongly negative "
            "despite lower DD — insurance claim not supported for that formulation."
        )
        if stance == "active":
            rec = "pivot"

    if mid == "tsmom_underreaction" and ft > 0:
        refuting.append("hyp_mom_30_pos: confirmatory failed (negative test Sharpe, MT, fees).")

    if mid == "herding_trend" and n >= 20 and pv == 0:
        stance = "exhausted_null"
        conf = 0.75
        rec = "retire"
        refuting.append("Heavy testing of SMA/EMA trend class; no confirmatory path so far.")

    return ThesisNode(
        mechanism_id=mid,
        name=name,
        claim=claim,
        stance=stance,
        confidence=min(0.95, conf),
        n_tests=n,
        n_passed_val=pv,
        n_failed_test=ft,
        n_candidate=cand,
        supporting=supporting[:8],
        refuting=refuting[:8],
        unknowns=unknowns[:6],
        recommendation=rec,
    )


def _write_tree(root: Path, tree: ThesisTree) -> None:
    paths = thesis_paths(root)
    paths["json"].parent.mkdir(parents=True, exist_ok=True)
    paths["json"].write_text(json.dumps(tree.to_dict(), indent=2))
    paths["md"].write_text(render_thesis_markdown(tree))


def render_thesis_markdown(tree: ThesisTree) -> str:
    lines = [
        "# Research Thesis Tree",
        "",
        f"**Updated:** `{tree.updated_at}`  ",
        f"**Summary:** {tree.summary}",
        "",
        "Epistemic map of *economic mechanisms*. Confidence = certainty about the "
        "**scientific status** of the claim, not expected returns.",
        "",
        "Nomination ≠ promotion: confirmatory still requires **existing validation gates**.",
        "",
        "## Global unknowns",
        "",
    ]
    for u in tree.global_unknowns:
        lines.append(f"- {u}")
    lines += ["", "## Mechanisms", ""]

    for n in tree.nodes:
        lines += [
            f"### `{n.mechanism_id}` — {n.name}",
            "",
            f"- **Stance:** `{n.stance}` (confidence {n.confidence:.2f})",
            f"- **Recommendation:** `{n.recommendation}`",
            f"- **Claim:** {n.claim}",
            f"- **Evidence mass:** n_tests={n.n_tests}, passed_val={n.n_passed_val}, "
            f"failed_test={n.n_failed_test}, candidate={n.n_candidate}",
            "",
            "**Supporting**",
            "",
        ]
        if n.supporting:
            for s in n.supporting:
                lines.append(f"- {s}")
        else:
            lines.append("- _(none logged)_")
        lines += ["", "**Refuting**", ""]
        if n.refuting:
            for s in n.refuting:
                lines.append(f"- {s}")
        else:
            lines.append("- _(none logged)_")
        lines += ["", "**Remaining unknowns**", ""]
        for u in n.unknowns:
            lines.append(f"- {u}")
        lines.append("")

    lines += [
        "---",
        "",
        "*Chief Research Scientist mode: maximise knowledge per budget unit.*",
        "",
    ]
    return "\n".join(lines)


def record_experiment_on_tree(
    root: Path,
    registry_path: Path,
    *,
    hyp_id: str,
    mechanism_ids: list[str],
    status: str,
    supports: str = "",
    refutes: str = "",
    unknown: str = "",
    family_decision: str = "",
) -> ThesisTree:
    """Update tree after a single experiment (rebuild + inject notes)."""
    note = {
        "hyp_id": hyp_id,
        "mechanism_ids": mechanism_ids,
        "status": status,
        "supports": supports,
        "refutes": refutes,
        "unknown": unknown,
        "family_decision": family_decision,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    # Persist experiment notes log
    log_path = root / "research_kb" / "experiment_notes.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(note) + "\n")

    notes: list[dict[str, Any]] = []
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            if line.strip():
                notes.append(json.loads(line))
    return rebuild_thesis_tree(registry_path, root, experiment_notes=notes)
