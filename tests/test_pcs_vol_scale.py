"""PCS vol-scale programme — structural tests (not promotion)."""

from __future__ import annotations

from crl.research.pcs.vol_scale import desired_inv_vol, evaluate_pcs_vol_scale
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.types import CostConfig, SplitConfig


def test_desired_inv_vol_bounds():
    ohlcv = MockOHLCVSource(n=300, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    w = desired_inv_vol(ohlcv, rv_window=20)
    assert w.min() >= 0.0
    assert w.max() <= 1.0
    assert w.notna().sum() > 50


def test_eval_runs_mock():
    ohlcv = MockOHLCVSource(n=400, seed=2).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    # ensure open for next_open
    if "open" not in ohlcv.columns:
        ohlcv = ohlcv.copy()
        ohlcv["open"] = ohlcv["close"] * 0.999
    rep = evaluate_pcs_vol_scale(
        ohlcv,
        costs=CostConfig(),
        splits=SplitConfig(train_frac=0.5, val_frac=0.25, test_frac=0.25),
    )
    assert rep["family_id"] == "pcs_vol_scale_v1"
    assert "confirmatory_pass" in rep
    assert "slices" in rep
