import numpy as np

from crl.research.backtest.engine import run_backtest
from crl.research.pipeline.run import prepare_frame, run_hypothesis_pipeline
from crl.shared.config import load_config
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.data.store import save_dataset
from crl.shared.types import CostConfig, HypothesisSpec, ResearchMode, RuleSpec, Taxonomy


def test_backtest_deterministic():
    df = MockOHLCVSource(n=500, seed=9).fetch_ohlcv("BTCUSDT", "1d")
    feat = prepare_frame(df).dropna(subset=["sma_200"])
    spec = HypothesisSpec(
        id="det",
        entry=RuleSpec(expression="close > sma_200"),
        exit=RuleSpec(expression="close < sma_200"),
    )
    c = CostConfig()
    a = run_backtest(feat, spec, c)
    b = run_backtest(feat, spec, c)
    assert np.allclose(a.equity.values, b.equity.values)


def test_pipeline_mock_end_to_end(tmp_path, monkeypatch):
    # run inside tmp by monkeypatching project_root? easier: use mock path via save in real project
    cfg = load_config()
    root_data = tmp_path
    df = MockOHLCVSource(n=1200, seed=11).fetch_ohlcv("BTCUSDT", "1d")
    # Use real project paths from config relative to cwd
    from crl.shared.config import project_root

    root = project_root()
    manifest = save_dataset(
        df,
        source="mock",
        symbol="BTCUSDT",
        interval="1d",
        processed_dir=root / "data" / "processed",
        manifest_dir=root / "data" / "manifests",
        source_class="mock",
    )
    spec = HypothesisSpec(
        id="hyp_e2e_mock",
        version=1,
        taxonomy=Taxonomy.COMPOSITE,
        entry=RuleSpec(expression="close > sma_200 and rvol_below_median > 0.5"),
        exit=RuleSpec(expression="close < sma_200"),
        rationale="E2E pipeline test of trend plus vol filter under synthetic data.",
        expected_outcome="Likely reject; validates plumbing not alpha.",
    )
    # unique id to avoid confirmatory lock collisions across runs
    import time

    spec.id = f"hyp_e2e_mock_{int(time.time())}"
    out = run_hypothesis_pipeline(
        spec, cfg, dataset_id=manifest.dataset_id, mode=ResearchMode.EXPLORATORY
    )
    assert "final_status" in out
    assert out["report_md"]
    assert "metrics" in out and "val" in out["metrics"]
