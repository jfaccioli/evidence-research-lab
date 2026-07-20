"""C5: total return from initial capital; first bar included; toy fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.backtest.engine import BacktestResult, buy_and_hold, run_backtest
from crl.research.stats.metrics import compute_metrics, max_drawdown
from crl.shared.types import CostConfig, HypothesisSpec, RuleSpec


def test_total_return_product_of_all_bars():
    idx = pd.date_range("2020-01-01", periods=3, freq="1D", tz="UTC")
    # hand path: r = [0.10, -0.05, 0.20]
    bar = pd.Series([0.10, -0.05, 0.20], index=idx)
    w0 = 1.0
    wealth = [w0 * 1.10, w0 * 1.10 * 0.95, w0 * 1.10 * 0.95 * 1.20]
    equity = pd.Series(wealth, index=idx)
    res = BacktestResult(
        equity=equity,
        position=pd.Series(1.0, index=idx),
        trades=[],
        bar_returns=bar,
        signals=pd.Series(1.0, index=idx),
        initial_equity=w0,
    )
    m = compute_metrics(res, timeframe="1d")
    expected = 1.10 * 0.95 * 1.20 - 1.0  # 0.254
    assert abs(m.total_return - expected) < 1e-12
    # Must NOT equal equity[-1]/equity[0]-1 which drops first bar:
    wrong = wealth[-1] / wealth[0] - 1.0
    assert abs(m.total_return - wrong) > 1e-6


def test_excess_return_hand_fixture():
    idx = pd.date_range("2020-01-01", periods=2, freq="1D", tz="UTC")
    # strat: +10%, +10% → total 21%
    # bh: +0%, +10% → total 10%
    s_bar = pd.Series([0.10, 0.10], index=idx)
    b_bar = pd.Series([0.00, 0.10], index=idx)
    s_eq = pd.Series([1.10, 1.21], index=idx)
    b_eq = pd.Series([1.00, 1.10], index=idx)
    strat = BacktestResult(
        equity=s_eq,
        position=pd.Series(1.0, index=idx),
        trades=[],
        bar_returns=s_bar,
        signals=pd.Series(1.0, index=idx),
        initial_equity=1.0,
    )
    bh = BacktestResult(
        equity=b_eq,
        position=pd.Series(1.0, index=idx),
        trades=[],
        bar_returns=b_bar,
        signals=pd.Series(1.0, index=idx),
        initial_equity=1.0,
    )
    # Fix b_eq: after first bar 0% wealth stays 1.0
    bh.equity = pd.Series([1.0, 1.10], index=idx)
    m = compute_metrics(strat, timeframe="1d", bh_result=bh)
    assert abs(m.total_return - 0.21) < 1e-12
    assert abs(m.excess_return_vs_bh - (0.21 - 0.10)) < 1e-12


def test_drawdown_hand_fixture():
    # wealth path from W0=1: after bars → 1.0, 1.2, 0.9  (via equity after each bar)
    # prepend W0: 1.0, 1.0, 1.2, 0.9 — wait equity after bar0 if r=0 is 1.0
    idx = pd.date_range("2020-01-01", periods=3, freq="1D", tz="UTC")
    equity = pd.Series([1.0, 1.2, 0.9], index=idx)
    mdd, _ = max_drawdown(equity, initial_equity=1.0)
    # peaks: 1,1,1.2,1.2 → dd at 0.9 is 0.9/1.2 - 1 = -0.25
    assert abs(mdd - 0.25) < 1e-12


def test_buy_and_hold_includes_first_bar_in_total_return():
    idx = pd.date_range("2020-01-01", periods=3, freq="1D", tz="UTC")
    # open path: 100, 110, 121 → gross open-to-open: 0.1, 0.1, last open-close 0
    df = pd.DataFrame(
        {
            "open": [100.0, 110.0, 121.0],
            "high": [101.0, 111.0, 122.0],
            "low": [99.0, 109.0, 120.0],
            "close": [110.0, 121.0, 121.0],
            "volume": [1.0, 1.0, 1.0],
        },
        index=idx,
    )
    costs = CostConfig(fee_bps_per_side=0, half_spread_bps=0, slippage_bps_per_side=0)
    res = buy_and_hold(df, costs)
    # gross: 110/100-1=0.1, 121/110-1=0.1, 121/121-1=0
    expected = 1.1 * 1.1 * 1.0 - 1.0
    assert abs(res.total_return - expected) < 1e-12
    m = compute_metrics(res, timeframe="1d")
    assert abs(m.total_return - expected) < 1e-12
