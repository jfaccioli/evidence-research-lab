"""Paper session historical walk."""

from __future__ import annotations

from pathlib import Path

from crl.production.paper.session import run_paper_session
from crl.shared.data.feature_store import load_or_build_features
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.types import HypothesisSpec, RuleSpec, Taxonomy


def test_paper_session_runs_on_mock(tmp_path: Path):
    ohlcv = MockOHLCVSource(n=400, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    feat = load_or_build_features(
        ohlcv, dataset_id="mock_paper", cache_dir=tmp_path / "feat", force=True
    )
    spec = HypothesisSpec(
        id="hyp_paper_sma50",
        taxonomy=Taxonomy.TREND,
        entry=RuleSpec(expression="above_sma_50 == 1"),
        exit=RuleSpec(expression="above_sma_50 == 0"),
        rationale="paper path smoke",
    )
    res = run_paper_session(
        spec,
        feat,
        starting_cash=50.0,
        journal_dir=tmp_path / "journal",
    )
    assert res.n_bars > 50
    assert res.equity_end is not None
    assert res.journal_path is not None
    assert Path(res.journal_path).exists()
