"""Look-ahead and causal feature tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.backtest.engine import desired_position_from_rules, run_backtest
from crl.shared.data.features import add_features, assert_no_lookahead_sma
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.types import CostConfig, HypothesisSpec, RuleSpec


def test_sma_matches_past_window_only():
    df = MockOHLCVSource(n=400, seed=2).fetch_ohlcv("BTCUSDT", "1d")
    feat = add_features(df)
    assert_no_lookahead_sma(feat, 200)


def test_expanding_median_is_causal():
    df = MockOHLCVSource(n=400, seed=3).fetch_ohlcv("BTCUSDT", "1d")
    feat = add_features(df)
    rvol = feat["rvol_20"]
    exp_med = feat["rvol_20_exp_median"]
    # Reconstruct expanding median with min_periods=20 on rvol series
    expected = rvol.expanding(min_periods=20).median()
    both = pd.concat([exp_med, expected], axis=1).dropna()
    assert np.allclose(both.iloc[:, 0].values, both.iloc[:, 1].values)
    # Early value must not use future rvol: tampering with the end must not change early medians
    feat2 = feat.copy()
    feat2.loc[feat2.index[-1], "rvol_20"] = 1e9
    # recompute only expanding median as pipeline does
    feat2["rvol_20_exp_median"] = feat2["rvol_20"].expanding(min_periods=20).median()
    mid = len(feat2) // 2
    assert abs(feat2["rvol_20_exp_median"].iloc[mid] - exp_med.iloc[mid]) < 1e-12


def test_position_is_lagged_one_bar():
    df = MockOHLCVSource(n=300, seed=4).fetch_ohlcv("BTCUSDT", "1d")
    feat = add_features(df).dropna(subset=["sma_50"])
    desired = desired_position_from_rules(feat, "close > sma_50", "close < sma_50")
    spec = HypothesisSpec(
        id="t",
        entry=RuleSpec(expression="close > sma_50"),
        exit=RuleSpec(expression="close < sma_50"),
    )
    res = run_backtest(feat, spec, CostConfig())
    # executed position on bar t equals desired on t-1
    assert np.allclose(res.position.iloc[1:].values, desired.iloc[:-1].values)
