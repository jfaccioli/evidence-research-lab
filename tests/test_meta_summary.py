from pathlib import Path

from crl.research.hypotheses.registry import HypothesisRegistry
from crl.research.meta.summary import taxonomy_survival_table
from crl.shared.types import HypothesisSpec, HypothesisStatus, RuleSpec, Taxonomy


def test_taxonomy_survival_empty(tmp_path: Path):
    assert taxonomy_survival_table(tmp_path / "missing.sqlite") == []


def test_taxonomy_survival_counts(tmp_path: Path):
    db = tmp_path / "r.sqlite"
    reg = HypothesisRegistry(db)
    for i, (tax, status) in enumerate(
        [
            (Taxonomy.TREND, HypothesisStatus.FAILED_VAL),
            (Taxonomy.TREND, HypothesisStatus.PASSED_VAL),
            (Taxonomy.VOLUME, HypothesisStatus.FAILED_VAL),
        ]
    ):
        spec = HypothesisSpec(
            id=f"h{i}",
            taxonomy=tax,
            entry=RuleSpec(expression="close > sma_50"),
            exit=RuleSpec(expression="close < sma_50"),
        )
        reg.upsert_hypothesis(spec, status)
    table = taxonomy_survival_table(db)
    by = {r["taxonomy"]: r for r in table}
    assert by["trend"]["n_ideas"] == 2
    assert by["trend"]["n_survived"] == 1
    assert abs(by["trend"]["survival_rate"] - 0.5) < 1e-9
