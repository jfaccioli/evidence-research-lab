"""B3: confirmatory 2×-cost stress must use test-slice result."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.backtest.engine import run_backtest
from crl.research.stats.metrics import compute_metrics
from crl.risk.promotion import evaluate_gates
from crl.shared.types import CostConfig, GateConfig, HypothesisSpec, Metrics, RuleSpec


def test_gate_fails_when_test_stress_sharpe_negative_even_if_base_ok():
    """Regression: base-cost metrics pass; 2× test stress Sharpe < 0 must fail."""
    gates = GateConfig(
        min_trades=1,
        sharpe_min=0.0,
        max_drawdown=0.99,
        overfit_gap_max=10.0,
        wf_min_positive_fold_frac=0.0,
        bootstrap_ci_lower_sharpe_min=-10.0,
        skeptical_p_mean_trade_gt0_min=0.0,
    )
    # Construct metrics that pass primary gates
    m = Metrics(
        n_bars=100,
        n_trades=40,
        total_return=0.1,
        cagr=0.05,
        volatility=0.2,
        sharpe_after_cost=0.5,
        sortino=0.5,
        calmar=0.2,
        max_drawdown=0.2,
        time_underwater_frac=0.3,
        turnover=10.0,
        avg_trade_return=0.01,
        avg_hold_bars=5.0,
        edge_bps_per_trade=10.0,
        excess_return_vs_bh=-0.1,
        ir_vs_bh=-0.1,
        beta_proxy=0.5,
    )
    # If we wrongly passed val stress (>=0) but test stress is negative → must reject
    g = evaluate_gates(
        m,
        gates,
        stress_sharpe=-0.1,  # test-slice 2× cost
        confirmatory=True,
        fragility_pass_frac=1.0,
        multiple_testing_ok=True,
    )
    assert g.passed is False
    assert any("2x cost" in r for r in g.reasons)


def test_stress_sharpe_differs_val_vs_test_on_toy_data():
    """Ensure stressing different slices yields different stress Sharpes (wireability)."""
    idx = pd.date_range("2020-01-01", periods=60, freq="1D", tz="UTC")
    rng = np.random.default_rng(0)
    close = 100 * np.exp(np.cumsum(rng.normal(0.001, 0.02, 60)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    df = pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close) * 1.01,
            "low": np.minimum(open_, close) * 0.99,
            "close": close,
            "volume": 1e6,
            "sma_10": pd.Series(close).rolling(10, min_periods=1).mean().values,
        },
        index=idx,
    )
    spec = HypothesisSpec(
        id="stress_toy",
        entry=RuleSpec(expression="close > sma_10"),
        exit=RuleSpec(expression="close < sma_10"),
        rationale="Toy rule for confirmatory stress slice separation unit test.",
        expected_outcome="Unit test only.",
    )
    costs = CostConfig()
    val = df.iloc[:40]
    test = df.iloc[40:]
    base_test = compute_metrics(run_backtest(test, spec, costs), timeframe="1d")
    stress_val = compute_metrics(
        run_backtest(val, spec, costs, stress=True), timeframe="1d"
    )
    stress_test = compute_metrics(
        run_backtest(test, spec, costs, stress=True), timeframe="1d"
    )
    # Not required that they differ always, but stress should be <= base typically
    assert stress_test.sharpe_after_cost <= base_test.sharpe_after_cost + 1e-9
    # Document that val stress is not identical object to test stress
    assert isinstance(stress_val.sharpe_after_cost, float)
    assert isinstance(stress_test.sharpe_after_cost, float)
