"""Analyse registry evidence before proposing new work."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from crl.research.planner.mechanisms import MECHANISMS, infer_mechanisms


@dataclass
class FamilyEvidence:
    family_id: str
    taxonomy: str
    n: int
    n_failed: int
    n_passed_val: int
    n_candidate: int
    n_failed_test: int
    common_reject_tags: list[tuple[str, int]]
    mechanisms: list[str]
    recommendation: str  # continue | pivot | retire
    rationale: str


@dataclass
class RegistryAnalysis:
    n_hypotheses: int
    n_runs: int
    taxonomies: dict[str, dict[str, Any]]
    families: list[FamilyEvidence]
    mechanism_coverage: dict[str, int]
    underrepresented_mechanisms: list[str]
    exhausted_families: list[str]
    repeating_failures: list[dict[str, Any]]
    explored_rule_fingerprints: set[str]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_hypotheses": self.n_hypotheses,
            "n_runs": self.n_runs,
            "taxonomies": self.taxonomies,
            "families": [
                {
                    "family_id": f.family_id,
                    "taxonomy": f.taxonomy,
                    "n": f.n,
                    "n_failed": f.n_failed,
                    "n_passed_val": f.n_passed_val,
                    "n_candidate": f.n_candidate,
                    "n_failed_test": f.n_failed_test,
                    "common_reject_tags": f.common_reject_tags,
                    "mechanisms": f.mechanisms,
                    "recommendation": f.recommendation,
                    "rationale": f.rationale,
                }
                for f in self.families
            ],
            "mechanism_coverage": self.mechanism_coverage,
            "underrepresented_mechanisms": self.underrepresented_mechanisms,
            "exhausted_families": self.exhausted_families,
            "repeating_failures": self.repeating_failures,
            "n_unique_rule_fingerprints": len(self.explored_rule_fingerprints),
            "notes": self.notes,
        }


def _rule_fingerprint(entry: str, exit_: str) -> str:
    """Normalize rule text to detect clones (ignore whitespace)."""
    e = re.sub(r"\s+", "", entry.lower())
    x = re.sub(r"\s+", "", exit_.lower())
    # collapse numeric literals slightly for near-clone detection
    e2 = re.sub(r"\d+\.?\d*", "N", e)
    x2 = re.sub(r"\d+\.?\d*", "N", x)
    return f"{e2}|{x2}"


def _tag_reason(reason: str) -> str:
    r = reason.lower()
    if "n_trades" in r:
        return "low_sample"
    if "reality" in r or "fee_fragile" in r or "economic_plausibility" in r:
        return "reality"
    if "sharpe" in r:
        return "weak_sharpe"
    if "overfit" in r:
        return "overfit"
    if "wf_" in r or "walk" in r:
        return "walk_forward"
    if "bootstrap" in r:
        return "bootstrap"
    if "fragility" in r:
        return "fragility"
    if "multiple-testing" in r or "multiple_testing" in r:
        return "multiple_testing"
    if "trust" in r:
        return "data_trust"
    if "budget" in r:
        return "budget"
    return "other"


def analyze_registry(registry_path: str | Path) -> RegistryAnalysis:
    path = Path(registry_path)
    if not path.exists():
        return RegistryAnalysis(
            n_hypotheses=0,
            n_runs=0,
            taxonomies={},
            families=[],
            mechanism_coverage={m.id: 0 for m in MECHANISMS},
            underrepresented_mechanisms=[m.id for m in MECHANISMS],
            exhausted_families=[],
            repeating_failures=[],
            explored_rule_fingerprints=set(),
            notes=["Empty registry — all mechanisms underrepresented."],
        )

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        hyps = conn.execute("SELECT * FROM hypotheses").fetchall()
        n_runs = int(conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"])
        events = conn.execute(
            "SELECT hypothesis_id, version, reason, to_status FROM events WHERE reason IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()

    tax: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    fam_rows: dict[str, list] = defaultdict(list)
    fingerprints: set[str] = set()
    mech_counts: Counter = Counter()
    reject_tags_global: Counter = Counter()

    for h in hyps:
        tax[h["taxonomy"] or "unknown"]["n"] += 1
        st = h["status"] or ""
        if st.startswith("failed") or st == "rejected":
            tax[h["taxonomy"] or "unknown"]["failed"] += 1
        if st == "passed_val":
            tax[h["taxonomy"] or "unknown"]["passed_val"] += 1
        if st == "candidate":
            tax[h["taxonomy"] or "unknown"]["candidate"] += 1
        if st == "failed_test":
            tax[h["taxonomy"] or "unknown"]["failed_test"] += 1

        fam = h["family_id"] or h["id"]
        fam_rows[fam].append(h)

        try:
            spec = json.loads(h["spec_json"] or "{}")
            entry = (spec.get("entry") or {}).get("expression", "")
            exit_ = (spec.get("exit") or {}).get("expression", "")
            if isinstance(spec.get("entry"), str):
                entry = spec["entry"]
            if isinstance(spec.get("exit"), str):
                exit_ = spec["exit"]
        except json.JSONDecodeError:
            entry, exit_ = "", ""
        fingerprints.add(_rule_fingerprint(entry, exit_))

        blob = " ".join(
            [
                h["id"] or "",
                h["rationale"] or "",
                entry,
                exit_,
                h["taxonomy"] or "",
            ]
        )
        for mid in infer_mechanisms(blob, taxonomy=h["taxonomy"] or ""):
            if mid != "unknown":
                mech_counts[mid] += 1

    # reject tags from events
    fam_tags: dict[str, Counter] = defaultdict(Counter)
    for ev in events:
        reason = (ev["reason"] or "").strip()
        # ignore lifecycle noise
        if reason.lower() in ("created", "pipeline start", "go", "test_unlocked_consumed", ""):
            continue
        if not any(
            k in reason.lower()
            for k in (
                "n_trades",
                "sharpe",
                "reality",
                "overfit",
                "wf_",
                "bootstrap",
                "fragility",
                "multiple",
                "trust",
                "budget",
                "failed",
                "reject",
            )
        ) and (ev["to_status"] or "") in ("draft", "running", None, ""):
            continue
        tag = _tag_reason(reason)
        if tag == "other" and (ev["to_status"] or "").startswith("failed") is False:
            if "fail" not in reason.lower() and "<" not in reason:
                continue
        reject_tags_global[tag] += 1
        for h in hyps:
            if h["id"] == ev["hypothesis_id"] and h["version"] == ev["version"]:
                fam_tags[h["family_id"] or h["id"]][tag] += 1
                break

    families: list[FamilyEvidence] = []
    exhausted: list[str] = []
    for fam, rows in sorted(fam_rows.items(), key=lambda x: -len(x[1])):
        n = len(rows)
        n_failed = sum(
            1 for r in rows if (r["status"] or "").startswith("failed") or r["status"] == "rejected"
        )
        n_pv = sum(1 for r in rows if r["status"] == "passed_val")
        n_cand = sum(1 for r in rows if r["status"] == "candidate")
        n_ft = sum(1 for r in rows if r["status"] == "failed_test")
        tags = fam_tags.get(fam, Counter()).most_common(5)
        tax0 = rows[0]["taxonomy"] or "unknown"
        blob = " ".join((r["rationale"] or "") + " " + (r["id"] or "") for r in rows)
        mechs = [
            m
            for m in infer_mechanisms(blob, taxonomy=tax0)
            if m != "unknown"
        ]
        mechs = list(dict.fromkeys(mechs))

        rec, why = _family_recommendation(n, n_failed, n_pv, n_cand, n_ft, tags)
        if rec == "retire":
            exhausted.append(fam)
        families.append(
            FamilyEvidence(
                family_id=fam,
                taxonomy=tax0,
                n=n,
                n_failed=n_failed,
                n_passed_val=n_pv,
                n_candidate=n_cand,
                n_failed_test=n_ft,
                common_reject_tags=tags,
                mechanisms=mechs,
                recommendation=rec,
                rationale=why,
            )
        )

    coverage = {m.id: int(mech_counts.get(m.id, 0)) for m in MECHANISMS}
    # underrepresented: 0 or bottom quartile
    counts = sorted(coverage.values())
    thr = counts[len(counts) // 4] if counts else 0
    under = [mid for mid, c in coverage.items() if c <= max(thr, 2)]
    under = sorted(under, key=lambda m: coverage[m])

    repeating = [
        {"tag": t, "count": c, "interpretation": _fail_interp(t)}
        for t, c in reject_tags_global.most_common(8)
    ]

    tax_out = {
        k: {
            "n": v["n"],
            "failed": v.get("failed", 0),
            "passed_val": v.get("passed_val", 0),
            "candidate": v.get("candidate", 0),
            "failed_test": v.get("failed_test", 0),
        }
        for k, v in tax.items()
    }

    notes = []
    if n_pv_total := sum(t.get("passed_val", 0) for t in tax_out.values()):
        notes.append(f"{n_pv_total} exploratory passed_val — still need confirmatory survivors.")
    if sum(t.get("candidate", 0) for t in tax_out.values()) == 0:
        notes.append("Zero confirmatory candidates in registry.")
    if under:
        notes.append(
            "Underrepresented mechanisms: " + ", ".join(under[:6])
        )

    return RegistryAnalysis(
        n_hypotheses=len(hyps),
        n_runs=n_runs,
        taxonomies=tax_out,
        families=families,
        mechanism_coverage=coverage,
        underrepresented_mechanisms=under,
        exhausted_families=exhausted,
        repeating_failures=repeating,
        explored_rule_fingerprints=fingerprints,
        notes=notes,
    )


def _family_recommendation(
    n: int,
    n_failed: int,
    n_pv: int,
    n_cand: int,
    n_ft: int,
    tags: list[tuple[str, int]],
) -> tuple[str, str]:
    if n_cand > 0:
        return "continue", "Has candidate — deepen robustness / paper path only after GO."
    if n_ft > 0 and n_pv > 0:
        return (
            "pivot",
            "Exploratory tease then confirmatory fail — do not clone; change mechanism.",
        )
    top = tags[0][0] if tags else ""
    if n >= 8 and n_failed >= n - 1 and top in ("low_sample", "weak_sharpe", "reality"):
        return (
            "retire",
            f"Large family ({n}) nearly all failed, dominant tag={top}; diminishing returns.",
        )
    if n >= 5 and n_failed == n and top == "low_sample":
        return (
            "pivot",
            "Repeated low sample — need higher-frequency decision rules or longer span, not more sparse filters.",
        )
    if n >= 3 and n_failed == n:
        return "pivot", "All failed — try different mechanism, not nearby params."
    if n <= 2:
        return "continue", "Thin evidence — one more *distinct* test may still inform."
    return "continue", "Mixed or small sample — selective continuation only."


def _fail_interp(tag: str) -> str:
    return {
        "low_sample": "Rules too sparse on daily bars — need more trades or different horizon.",
        "reality": "Statistically cute but economically/executionally weak.",
        "weak_sharpe": "No risk-adjusted edge after costs on evaluated splits.",
        "overfit": "Train much stronger than val/test — stop fitting narrative.",
        "walk_forward": "Unstable across time folds.",
        "bootstrap": "Point estimate not supported under resampling.",
        "fragility": "Parameter neighborhood collapses — not robust.",
        "multiple_testing": "Selection / family size kills significance.",
        "other": "See event reasons in registry.",
    }.get(tag, "See registry events.")
