"""Information-gain scoring for proposed experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from crl.research.planner.analyze import RegistryAnalysis
from crl.research.planner.mechanisms import MECH_BY_ID


@dataclass
class InformationGainScore:
    total: float
    novelty_mechanism: float
    assumption_invalidation: float
    expected_value_if_true: float
    anti_clone: float
    budget_efficiency: float
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": round(self.total, 3),
            "novelty_mechanism": round(self.novelty_mechanism, 3),
            "assumption_invalidation": round(self.assumption_invalidation, 3),
            "expected_value_if_true": round(self.expected_value_if_true, 3),
            "anti_clone": round(self.anti_clone, 3),
            "budget_efficiency": round(self.budget_efficiency, 3),
            "notes": self.notes,
        }


def score_information_gain(
    *,
    mechanism_ids: list[str],
    rule_fingerprint: str,
    analysis: RegistryAnalysis,
    invalidates_assumption: str = "",
    expected_value_if_true: str = "",
    near_exhausted_family: bool = False,
) -> InformationGainScore:
    """Higher = more knowledge expected per budget unit.

    Components in [0, 1] roughly; total is weighted sum.
    """
    notes: list[str] = []
    cov = analysis.mechanism_coverage

    # 1) Novelty: prefer zero/low coverage mechanisms
    novs = []
    for mid in mechanism_ids:
        c = cov.get(mid, 0)
        if c == 0:
            novs.append(1.0)
            notes.append(f"mechanism {mid} unexplored")
        elif c <= 2:
            novs.append(0.75)
            notes.append(f"mechanism {mid} thin (n={c})")
        elif c <= 5:
            novs.append(0.4)
        else:
            novs.append(0.15)
            notes.append(f"mechanism {mid} already heavily tested (n={c})")
    novelty = max(novs) if novs else 0.2

    # 2) Assumption invalidation: text present + targets a repeating failure or popular assumption
    inv = 0.2
    if invalidates_assumption and len(invalidates_assumption) > 20:
        inv = 0.7
        low = invalidates_assumption.lower()
        for fail in analysis.repeating_failures[:3]:
            if fail["tag"] in low or fail["tag"].replace("_", " ") in low:
                inv = 1.0
                notes.append(f"targets repeating failure tag={fail['tag']}")
                break
        if "buy" in low and "hold" in low:
            inv = max(inv, 0.85)
            notes.append("could challenge B&H / beta assumption")
    else:
        notes.append("weak assumption-invalidation statement")

    # 3) EV if true (qualitative → score)
    ev = 0.3
    evt = (expected_value_if_true or "").lower()
    if len(evt) > 30:
        ev = 0.55
    if any(w in evt for w in ("drawdown", "tail", "crash", "asymmetric", "capacity", "aud")):
        ev = 0.8
        notes.append("high practical EV if true (risk/capital relevant)")
    if "alpha" in evt and "beta" in evt:
        ev = max(ev, 0.7)

    # 4) Anti-clone: fingerprint already seen?
    if rule_fingerprint in analysis.explored_rule_fingerprints:
        anti = 0.0
        notes.append("CLONE: rule fingerprint already explored — IG collapsed")
    else:
        # structural near-clones already partially handled by fingerprint N-collapse
        anti = 1.0
        # if only over-tested mechanisms, reduce
        if novelty < 0.3:
            anti = 0.4
            notes.append("novel rule text but same over-tested mechanism class")

    if near_exhausted_family:
        anti *= 0.3
        notes.append("family marked retire/pivot — heavy IG penalty")

    # 5) Budget efficiency: reward high novelty + anti-clone (knowledge density)
    budget_eff = 0.5 * novelty + 0.5 * anti

    total = (
        0.30 * novelty
        + 0.25 * inv
        + 0.15 * ev
        + 0.20 * anti
        + 0.10 * budget_eff
    )
    # hard floor for clones
    if anti == 0.0:
        total = min(total, 0.05)

    # name mechanisms for notes
    for mid in mechanism_ids:
        if mid in MECH_BY_ID:
            notes.append(f"maps to: {MECH_BY_ID[mid].name}")

    return InformationGainScore(
        total=total,
        novelty_mechanism=novelty,
        assumption_invalidation=inv,
        expected_value_if_true=ev,
        anti_clone=anti,
        budget_efficiency=budget_eff,
        notes=notes,
    )
