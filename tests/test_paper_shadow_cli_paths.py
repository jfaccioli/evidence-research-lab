"""Paper replay + shadow walk reliability."""

from pathlib import Path

from crl.production.paper.replay import replay_hyp_dir, write_replay_summary
from crl.production.shadow.walk import shadow_walk
from crl.research.pipeline.batch import load_hypothesis_yaml
from crl.shared.data.feature_store import load_or_build_features
from crl.shared.data.sources.mock import MockOHLCVSource


def test_replay_and_shadow_on_mock(tmp_path: Path):
    ohlcv = MockOHLCVSource(n=350, seed=3).fetch_ohlcv("BTCUSDT", "1d")
    feat = load_or_build_features(
        ohlcv, dataset_id="mock_ops", cache_dir=tmp_path / "f", force=True
    )
    # minimal one-file hyp dir
    hyp_dir = tmp_path / "hyps"
    hyp_dir.mkdir()
    (hyp_dir / "hyp_ops_sma50.yaml").write_text(
        """
id: hyp_ops_sma50
version: 1
asset: BTC/USDT
timeframe: 1d
taxonomy: trend
entry:
  expression: above_sma_50 == 1
exit:
  expression: above_sma_50 == 0
rationale: ops smoke
"""
    )
    rows = replay_hyp_dir(
        hyp_dir, feat, starting_cash=50.0, journal_dir=tmp_path / "j"
    )
    assert len(rows) == 1
    assert rows[0]["n_bars"] > 50
    assert "max_drawdown" in rows[0]
    summary = write_replay_summary(rows, tmp_path / "sum.json")
    assert summary.exists()

    spec = load_hypothesis_yaml(hyp_dir / "hyp_ops_sma50.yaml")
    sh = shadow_walk(spec, feat, log_dir=tmp_path / "shadow")
    assert sh["n_bars"] > 50
    assert sh["log_path"] is not None
