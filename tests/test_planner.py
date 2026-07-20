"""Evidence-driven research planner tests."""

from pathlib import Path

from crl.research.hypotheses.registry import HypothesisRegistry
from crl.research.planner.analyze import analyze_registry, _rule_fingerprint
from crl.research.planner.budget import ResearchBudget
from crl.research.planner.plan import build_research_plan, update_knowledge_after_batch
from crl.research.planner.proposals import generate_ranked_proposals
from crl.research.planner.score import score_information_gain
from crl.shared.types import HypothesisSpec, HypothesisStatus, RuleSpec, Taxonomy


def _seed_registry(path: Path, n_trend: int = 5) -> None:
    reg = HypothesisRegistry(path)
    for i in range(n_trend):
        spec = HypothesisSpec(
            id=f"hyp_trend_{i}",
            taxonomy=Taxonomy.TREND,
            family_id="family_trend",
            entry=RuleSpec(expression=f"close > sma_{50 + i * 10}"),
            exit=RuleSpec(expression=f"close < sma_{50 + i * 10}"),
            rationale="Herding trend following capital flow test for planner coverage analysis unit.",
            expected_outcome="Expect fail; used only to populate registry for planner tests.",
        )
        reg.upsert_hypothesis(spec, HypothesisStatus.FAILED_VAL)
        reg.transition(spec.id, 1, HypothesisStatus.FAILED_VAL, "n_trades 3 < min_trades 30")


def test_fingerprint_near_clone():
    a = _rule_fingerprint("close > sma_50", "close < sma_50")
    b = _rule_fingerprint("close > sma_200", "close < sma_200")
    assert a == b  # numeric collapsed


def test_analyze_empty(tmp_path: Path):
    a = analyze_registry(tmp_path / "missing.sqlite")
    assert a.n_hypotheses == 0
    assert len(a.underrepresented_mechanisms) > 0


def test_analyze_and_plan(tmp_path: Path):
    db = tmp_path / "r.sqlite"
    _seed_registry(db, 6)
    analysis = analyze_registry(db)
    assert analysis.n_hypotheses == 6
    assert "family_trend" in [f.family_id for f in analysis.families]
    props = generate_ranked_proposals(analysis, max_n=3, min_ig=0.2)
    assert len(props) >= 1
    p0 = props[0]
    assert p0.economic_rationale
    assert p0.falsification_criteria
    assert p0.why_different
    assert p0.expected_failure_modes
    assert p0.information_gain.total > 0


def test_clone_scores_near_zero(tmp_path: Path):
    db = tmp_path / "r.sqlite"
    reg = HypothesisRegistry(db)
    spec = HypothesisSpec(
        id="hyp_exact",
        taxonomy=Taxonomy.CALENDAR,
        family_id="family_calendar",
        entry=RuleSpec(expression="is_weekend < 0.5"),
        exit=RuleSpec(expression="is_weekend > 0.5"),
        rationale="Calendar weekday-only long test for clone detection in planner scoring.",
        expected_outcome="Reject if no weekend effect after costs.",
    )
    reg.upsert_hypothesis(spec, HypothesisStatus.FAILED_VAL)
    analysis = analyze_registry(db)
    fp = _rule_fingerprint("is_weekend < 0.5", "is_weekend > 0.5")
    ig = score_information_gain(
        mechanism_ids=["calendar_seasonality"],
        rule_fingerprint=fp,
        analysis=analysis,
        invalidates_assumption="Tests weekend effect assumption in BTC markets thoroughly.",
        expected_value_if_true="If true, simple operational calendar rule for desks.",
    )
    assert ig.anti_clone == 0.0
    assert ig.total <= 0.05


def test_budget_spend(tmp_path: Path):
    b = ResearchBudget(path=tmp_path / "b.json", units_total=10, units_spent=0)
    b.spend(mode="exploratory", hyp_id="h1")
    assert b.units_remaining == 9
    b.spend(mode="confirmatory", hyp_id="h2")
    assert b.units_remaining == 4


def test_build_plan_writes(tmp_path: Path, monkeypatch):
    db = tmp_path / "reg" / "crl.sqlite"
    db.parent.mkdir(parents=True)
    _seed_registry(db, 4)
    root = tmp_path / "proj"
    root.mkdir()
    (root / "configs").mkdir()
    plan = build_research_plan(
        registry_path=db,
        root=root,
        cfg={"planner": {"min_information_gain": 0.2, "max_proposals": 3}},
        write_artifacts=True,
    )
    assert (root / "research_kb" / "latest_plan.md").exists()
    assert plan.paths.get("plan_md")
    update_knowledge_after_batch(registry_path=db, root=root)
    assert (root / "research_kb" / "LEARNINGS.md").exists()
