"""Orchestrate evidence-driven research plans."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from crl.research.planner.analyze import RegistryAnalysis, analyze_registry
from crl.research.planner.budget import ResearchBudget
from crl.research.planner.knowledge import knowledge_paths, update_knowledge_base
from crl.research.planner.proposals import ResearchProposal, generate_ranked_proposals


@dataclass
class ResearchPlan:
    created_at: str
    analysis: RegistryAnalysis
    budget: dict[str, Any]
    proposals: list[ResearchProposal]
    recommendations: list[str] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "budget": self.budget,
            "recommendations": self.recommendations,
            "analysis_summary": {
                "n_hypotheses": self.analysis.n_hypotheses,
                "underrepresented_mechanisms": self.analysis.underrepresented_mechanisms,
                "exhausted_families": self.analysis.exhausted_families,
                "repeating_failures": self.analysis.repeating_failures,
                "notes": self.analysis.notes,
                "taxonomies": self.analysis.taxonomies,
            },
            "proposals": [p.to_dict() for p in self.proposals],
            "paths": self.paths,
        }


def build_research_plan(
    *,
    registry_path: Path,
    root: Path,
    cfg: dict[str, Any] | None = None,
    write_artifacts: bool = True,
) -> ResearchPlan:
    cfg = cfg or {}
    pcfg = cfg.get("planner", {})
    paths = knowledge_paths(root)
    budget = ResearchBudget.load(paths["budget"], defaults=pcfg.get("budget"))
    analysis = analyze_registry(registry_path)
    # Attribute historical experiments to budget once (knowledge already bought)
    if not budget.history and analysis.n_hypotheses > 0 and budget.units_spent == 0:
        budget.units_spent = min(
            budget.units_total * 0.95,
            float(analysis.n_hypotheses) * budget.cost_per_exploratory,
        )
        budget.history.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "mode": "exploratory",
                "hyp_id": "_historical_backfill",
                "cost": budget.units_spent,
                "note": f"backfill {analysis.n_hypotheses} prior hyps",
                "remaining": budget.units_remaining,
            }
        )
        budget.save()
    max_n = min(
        budget.max_proposals_per_plan,
        int(pcfg.get("max_proposals", budget.max_proposals_per_plan)),
    )
    min_ig = float(pcfg.get("min_information_gain", 0.35))

    if budget.depleted:
        proposals: list[ResearchProposal] = []
        recs = [
            "Research budget exhausted — stop exploratory peeks; review KB and raise "
            "budget only deliberately (not to fish for winners)."
        ]
    else:
        proposals = generate_ranked_proposals(
            analysis, max_n=max_n, min_ig=min_ig
        )
        recs = _recommendations(analysis, proposals, budget)

    plan = ResearchPlan(
        created_at=datetime.now(timezone.utc).isoformat(),
        analysis=analysis,
        budget=budget.to_dict(),
        proposals=proposals,
        recommendations=recs,
    )

    if write_artifacts:
        paths["dir"].mkdir(parents=True, exist_ok=True)
        out_json = paths["dir"] / "latest_plan.json"
        out_md = paths["dir"] / "latest_plan.md"
        out_json.write_text(json.dumps(plan.to_dict(), indent=2, default=str))
        out_md.write_text(render_plan_markdown(plan))
        # optional YAML proposals for later registration
        prop_dir = paths["dir"] / "proposed"
        prop_dir.mkdir(exist_ok=True)
        for p in proposals:
            ypath = prop_dir / f"{p.id}.yaml"
            ypath.write_text(
                yaml.safe_dump(
                    {
                        "id": p.id,
                        "version": 1,
                        "asset": "BTC/USDT",
                        "timeframe": "1d",
                        "taxonomy": p.taxonomy,
                        "family_id": p.family_id,
                        "entry": {"expression": p.entry},
                        "exit": {"expression": p.exit},
                        "rationale": p.economic_rationale,
                        "expected_outcome": p.falsification_criteria,
                        "planner": {
                            "information_gain": p.information_gain.to_dict(),
                            "why_different": p.why_different,
                            "expected_failure_modes": p.expected_failure_modes,
                            "invalidates_assumption": p.invalidates_assumption,
                            "expected_value_if_true": p.expected_value_if_true,
                            "mechanism_ids": p.mechanism_ids,
                        },
                    },
                    sort_keys=False,
                    allow_unicode=True,
                )
            )
        plan.paths = {
            "plan_json": str(out_json),
            "plan_md": str(out_md),
            "proposed_dir": str(prop_dir),
            "learnings": str(paths["log"]),
            "budget": str(paths["budget"]),
        }
        if not paths["budget"].exists():
            budget.save()

    return plan


def update_knowledge_after_batch(
    *,
    registry_path: Path,
    root: Path,
    batch_summary: dict[str, Any] | None = None,
    spend_units: float | None = None,
    mode: str = "exploratory",
    hyp_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Call after batch completes: KB update + optional budget spend."""
    paths = knowledge_paths(root)
    budget = ResearchBudget.load(paths["budget"])
    if spend_units is not None:
        # spend per hyp if ids given
        if hyp_ids:
            for hid in hyp_ids:
                if budget.can_afford(mode):
                    try:
                        budget.spend(mode=mode, hyp_id=hid, note="batch")
                    except RuntimeError:
                        break
        elif spend_units > 0 and budget.can_afford(mode):
            budget.spend(mode=mode, hyp_id="batch", note=f"bulk {spend_units}")

    state = update_knowledge_base(registry_path, root, batch_summary=batch_summary)
    state["budget"] = budget.to_dict()
    return state


def _recommendations(
    analysis: RegistryAnalysis,
    proposals: list[ResearchProposal],
    budget: ResearchBudget,
) -> list[str]:
    recs = [
        f"Budget: {budget.units_remaining:.1f}/{budget.units_total:.1f} units remaining "
        f"(exploratory cost={budget.cost_per_exploratory}, confirmatory={budget.cost_per_confirmatory}).",
        "Objective: maximise knowledge per experiment — not hypothesis count or win rate.",
    ]
    if analysis.underrepresented_mechanisms:
        recs.append(
            "Underrepresented mechanisms to prefer: "
            + ", ".join(analysis.underrepresented_mechanisms[:5])
        )
    if analysis.exhausted_families:
        recs.append(
            f"Retire/avoid cloning {len(analysis.exhausted_families)} exhausted families."
        )
    for rf in analysis.repeating_failures[:3]:
        recs.append(f"Repeating failure **{rf['tag']}**: {rf['interpretation']}")
    if not proposals:
        recs.append(
            "No high-IG proposals passed filters — expand candidate pool carefully "
            "or accept that current search frontier is thin."
        )
    else:
        recs.append(
            f"Top proposal `{proposals[0].id}` IG={proposals[0].information_gain.total:.2f} "
            f"— run exploratorily via same frozen pipeline only if budget allows."
        )
    recs.append("Do not paper/live trade. Do not soften gates.")
    return recs


def render_plan_markdown(plan: ResearchPlan) -> str:
    lines = [
        "# Evidence-driven research plan",
        "",
        f"Created: `{plan.created_at}`",
        "",
        "## Budget",
        "",
        f"- remaining: **{plan.budget.get('units_remaining')}** / {plan.budget.get('units_total')}",
        f"- spent: {plan.budget.get('units_spent')}",
        "",
        "## Recommendations",
        "",
    ]
    for r in plan.recommendations:
        lines.append(f"- {r}")
    a = plan.to_dict()["analysis_summary"]
    lines += [
        "",
        "## Registry evidence",
        "",
        f"- n_hypotheses: {a['n_hypotheses']}",
        f"- underrepresented: {', '.join(a['underrepresented_mechanisms'][:8])}",
        "",
        "### Repeating failures",
        "",
    ]
    for rf in a["repeating_failures"][:6]:
        lines.append(f"- **{rf['tag']}** (n={rf['count']}): {rf['interpretation']}")
    lines += ["", "## Proposed experiments (ranked by information gain)", ""]
    if not plan.proposals:
        lines.append("_No proposals above IG threshold / budget._")
    for p in plan.proposals:
        ig = p.information_gain
        lines += [
            f"### {p.priority_rank}. `{p.id}` — IG **{ig.total:.3f}**",
            "",
            f"- **mechanisms:** {', '.join(p.mechanism_ids)}",
            f"- **entry:** `{p.entry}`",
            f"- **exit:** `{p.exit}`",
            f"- **economic rationale:** {p.economic_rationale}",
            f"- **falsification:** {p.falsification_criteria}",
            f"- **why different:** {p.why_different}",
            f"- **expected failure modes:** {p.expected_failure_modes}",
            f"- **invalidates assumption:** {p.invalidates_assumption}",
            f"- **EV if true:** {p.expected_value_if_true}",
            f"- **IG breakdown:** novelty={ig.novelty_mechanism:.2f} "
            f"invalidate={ig.assumption_invalidation:.2f} "
            f"ev={ig.expected_value_if_true:.2f} anti_clone={ig.anti_clone:.2f}",
            "",
        ]
    lines += [
        "## Process rules",
        "",
        "- Same frozen validation pipeline only.",
        "- Never weaken scientific standards.",
        "- No live/paper trading from this module.",
        "- Null results that retire a mechanism are successful learning.",
        "",
    ]
    return "\n".join(lines)
