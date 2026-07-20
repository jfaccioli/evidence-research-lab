from pathlib import Path

from crl.research.hypotheses.registry import HypothesisRegistry
from crl.research.planner.thesis_tree import rebuild_thesis_tree, record_experiment_on_tree
from crl.shared.types import HypothesisSpec, HypothesisStatus, RuleSpec, Taxonomy


def test_rebuild_empty(tmp_path: Path):
    root = tmp_path / "p"
    root.mkdir()
    tree = rebuild_thesis_tree(tmp_path / "missing.sqlite", root)
    assert len(tree.nodes) >= 5
    assert any(n.stance == "untested" for n in tree.nodes)
    assert (root / "research_kb" / "THESIS_TREE.md").exists()


def test_record_experiment(tmp_path: Path):
    root = tmp_path / "p"
    root.mkdir()
    db = tmp_path / "r.sqlite"
    reg = HypothesisRegistry(db)
    spec = HypothesisSpec(
        id="plan_asymmetric_capture_vol_gate",
        taxonomy=Taxonomy.COMPOSITE,
        family_id="family_mech_asymmetric_capture",
        entry=RuleSpec(expression="close > sma_200 and rvol_20_chg < 0.1"),
        exit=RuleSpec(expression="close < sma_100 or rvol_20_chg > 0.25"),
        rationale="Insurance-like asymmetric capture test for thesis tree unit tests.",
        expected_outcome="Expect fail; unit test seed only.",
    )
    reg.upsert_hypothesis(spec, HypothesisStatus.FAILED_VAL)
    tree = record_experiment_on_tree(
        root,
        db,
        hyp_id=spec.id,
        mechanism_ids=["asymmetric_capture", "vol_regime_shift"],
        status="failed_val",
        refutes="excess vs B&H negative; insurance claim weak for this formulation",
        family_decision="pivot",
    )
    node = next(n for n in tree.nodes if n.mechanism_id == "asymmetric_capture")
    assert node.n_tests >= 1
    assert any("excess" in r.lower() or "insurance" in r.lower() for r in node.refuting) or node.recommendation in (
        "pivot",
        "retire",
        "observe",
    )
