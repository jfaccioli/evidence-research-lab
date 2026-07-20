"""Finite research budget — knowledge per unit cost, not hyp count."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BUDGET = {
    "units_total": 100.0,  # lifetime exploratory units this phase
    "units_spent": 0.0,
    "cost_per_exploratory": 1.0,
    "cost_per_confirmatory": 5.0,  # test set peeks are expensive
    "max_proposals_per_plan": 5,
    "max_same_mechanism_in_flight": 2,
}


@dataclass
class ResearchBudget:
    path: Path
    units_total: float = 100.0
    units_spent: float = 0.0
    cost_per_exploratory: float = 1.0
    cost_per_confirmatory: float = 5.0
    max_proposals_per_plan: int = 5
    max_same_mechanism_in_flight: int = 2
    history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def units_remaining(self) -> float:
        return max(0.0, self.units_total - self.units_spent)

    @property
    def depleted(self) -> bool:
        return self.units_remaining < self.cost_per_exploratory

    def can_afford(self, mode: str = "exploratory") -> bool:
        cost = (
            self.cost_per_confirmatory
            if mode == "confirmatory"
            else self.cost_per_exploratory
        )
        return self.units_remaining >= cost

    def spend(self, *, mode: str, hyp_id: str, note: str = "") -> float:
        cost = (
            self.cost_per_confirmatory
            if mode == "confirmatory"
            else self.cost_per_exploratory
        )
        if self.units_remaining < cost:
            raise RuntimeError(
                f"Research budget exhausted (need {cost}, have {self.units_remaining:.1f})"
            )
        self.units_spent += cost
        self.history.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "hyp_id": hyp_id,
                "cost": cost,
                "note": note,
                "remaining": self.units_remaining,
            }
        )
        self.save()
        return cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "units_total": self.units_total,
            "units_spent": self.units_spent,
            "units_remaining": self.units_remaining,
            "cost_per_exploratory": self.cost_per_exploratory,
            "cost_per_confirmatory": self.cost_per_confirmatory,
            "max_proposals_per_plan": self.max_proposals_per_plan,
            "max_same_mechanism_in_flight": self.max_same_mechanism_in_flight,
            "history": self.history[-50:],  # tail
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "units_total": self.units_total,
            "units_spent": self.units_spent,
            "cost_per_exploratory": self.cost_per_exploratory,
            "cost_per_confirmatory": self.cost_per_confirmatory,
            "max_proposals_per_plan": self.max_proposals_per_plan,
            "max_same_mechanism_in_flight": self.max_same_mechanism_in_flight,
            "history": self.history,
        }
        self.path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path, defaults: dict | None = None) -> "ResearchBudget":
        d = {**DEFAULT_BUDGET, **(defaults or {})}
        if path.exists():
            raw = json.loads(path.read_text())
            d.update({k: raw[k] for k in d if k in raw})
            hist = raw.get("history", [])
        else:
            hist = []
        b = cls(
            path=path,
            units_total=float(d["units_total"]),
            units_spent=float(d["units_spent"]),
            cost_per_exploratory=float(d["cost_per_exploratory"]),
            cost_per_confirmatory=float(d["cost_per_confirmatory"]),
            max_proposals_per_plan=int(d["max_proposals_per_plan"]),
            max_same_mechanism_in_flight=int(d["max_same_mechanism_in_flight"]),
            history=list(hist),
        )
        return b
