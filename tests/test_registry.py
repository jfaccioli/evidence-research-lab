from pathlib import Path

from crl.research.hypotheses.registry import HypothesisRegistry
from crl.shared.types import HypothesisSpec, HypothesisStatus, ResearchMode, RuleSpec


def test_registry_lifecycle(tmp_path: Path):
    reg = HypothesisRegistry(tmp_path / "t.sqlite")
    spec = HypothesisSpec(
        id="hyp_test",
        entry=RuleSpec(expression="close > sma_50"),
        exit=RuleSpec(expression="close < sma_50"),
    )
    reg.upsert_hypothesis(spec, HypothesisStatus.DRAFT)
    reg.transition("hyp_test", 1, HypothesisStatus.RUNNING, "go")
    run_id = reg.start_run("hyp_test", 1, ResearchMode.EXPLORATORY)
    reg.add_metrics(run_id, "val", {"sharpe_after_cost": 0.1})
    reg.finish_run(run_id, report_path="x.md")
    row = reg.get_hypothesis("hyp_test", 1)
    assert row["status"] == "running"
    rows = reg.list_hypotheses()
    assert len(rows) == 1


def test_confirmatory_lock(tmp_path: Path):
    reg = HypothesisRegistry(tmp_path / "t2.sqlite")
    spec = HypothesisSpec(
        id="hyp_lock",
        entry=RuleSpec(expression="close > sma_50"),
        exit=RuleSpec(expression="close < sma_50"),
    )
    reg.upsert_hypothesis(spec)
    reg.mark_saw_test("hyp_lock", 1)
    try:
        reg.assert_confirmatory_allowed("hyp_lock", 1, spec)
        assert False, "should have raised"
    except RuntimeError:
        pass
