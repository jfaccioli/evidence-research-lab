"""PR6 synthetic/mock contamination filters."""

from __future__ import annotations

import pytest

from crl.research.evidence.filters import (
    EvidenceRow,
    assert_no_synthetic_in_promotable_export,
    filter_promotable_evidence,
    is_synthetic_evidence,
)
from crl.research.ledger.trials import TrialKind


def _row(**kwargs) -> EvidenceRow:
    base = dict(
        trial_id="t1",
        trial_kind=TrialKind.HYPOTHESIS_EVAL.value,
        synthetic=False,
        selection_capable=True,
        is_citation=False,
        programme_version_id="pv1",
        research_lineage_id="rl1",
        selection_unit_id="su1",
    )
    base.update(kwargs)
    return EvidenceRow(**base)


def test_synthetic_flag_and_fixture_kind_excluded():
    assert is_synthetic_evidence(_row(synthetic=True))
    assert is_synthetic_evidence(
        _row(trial_kind=TrialKind.SYNTHETIC_FIXTURE.value)
    )
    assert is_synthetic_evidence(_row(dataset_id="mock_BTCUSDT_1d"))
    assert is_synthetic_evidence(_row(source_class="synthetic_fixture"))


def test_filter_promotable_removes_synthetic_and_citations():
    rows = [
        _row(trial_id="ok", synthetic=False),
        _row(trial_id="syn", synthetic=True),
        _row(trial_id="cit", is_citation=True),
        _row(trial_id="bh", trial_kind=TrialKind.BENCHMARK_BH.value),
        _row(trial_id="mockds", dataset_id="mock_series"),
    ]
    out = filter_promotable_evidence(rows)
    assert [r.trial_id for r in out] == ["ok"]


def test_assert_no_synthetic_in_export():
    assert_no_synthetic_in_promotable_export([_row(trial_id="ok")])
    with pytest.raises(ValueError, match="synthetic"):
        assert_no_synthetic_in_promotable_export(
            [_row(trial_id="bad", synthetic=True)]
        )
