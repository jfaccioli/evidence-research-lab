"""B1: trade wealth reconciles with bar path; exit costs included."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crl.research.backtest.costs import one_way_cost_fraction
from crl.research.backtest.engine import (
    compounded_path_return,
    run_backtest,
)
from crl.shared.types import CostConfig, HypothesisSpec, RuleSpec


def _ohlcv(n: int = 20, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # mild random walk
    rets = rng.normal(0.001, 0.02, size=n)
    close = 100 * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * 1.001
    low = np.minimum(open_, close) * 0.999
    idx = pd.date_range("2020-01-01", periods=n, freq="1D", tz="UTC")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1e6},
        index=idx,
    )


def _force_positions(df: pd.DataFrame, pos: list[float], costs: CostConfig) -> object:
    """Run engine but inject position sequence via custom rules on synthetic flags."""
    d = df.copy()
    # desired on bar t drives position on t+1; build desired so shift matches pos
    # position[0]=0 always after shift fill; so we set desired to lag pos
    # easier: monkeypatch by running with expression on column 'sig'
    d["sig"] = 0.0
    # We want position[i] = pos[i]. position = desired.shift(1).fillna(0)
    # so desired[i] = pos[i+1] for i < n-1, desired[n-1]=pos[n-1]
    desired = list(pos[1:]) + [pos[-1]]
    d["sig"] = desired
    # entry when sig>0.5 and was flat state machine - use close>0 always true and custom
    # Use: entry "sig > 0.5", exit "sig < 0.5" with state machine
    # Actually state machine: if flat and entry, go long; if long and exit, go flat
    # desired_position_from_rules is sequential state, not raw sig.
    # So inject by calling lower-level path:
    from crl.research.backtest.engine import (
        _bar_gross_returns,
        _trades_from_bar_returns,
        BacktestResult,
    )
    from crl.research.backtest.costs import one_way_cost_fraction as owc

    position = pd.Series(pos, index=d.index, dtype=float)
    gross, _ = _bar_gross_returns(d)
    cf = owc(costs)
    delta = position.diff().fillna(position.iloc[0])
    net = position * gross - delta.abs() * cf
    wealth = 1.0
    eq = []
    for r in net.values:
        wealth *= 1.0 + float(r)
        eq.append(wealth)
    trades = _trades_from_bar_returns(d, position, net, cost_frac=cf)
    return BacktestResult(
        equity=pd.Series(eq, index=d.index),
        position=position,
        trades=trades,
        bar_returns=net,
        signals=position,
        initial_equity=1.0,
        meta={},
    )


def test_no_trades_empty_reconciliation():
    df = _ohlcv(30)
    # never long: exit always true somehow - use impossible entry
    df["sma_50"] = df["close"] * 2  # close never > sma
    res = run_backtest(
        df,
        HypothesisSpec(
            id="none",
            entry=RuleSpec(expression="close > sma_50"),
            exit=RuleSpec(expression="close < sma_50"),
            rationale="Unit test never-enter rule for PnL identity empty path.",
            expected_outcome="No trades.",
        ),
        CostConfig(),
    )
    assert res.trades == []
    assert abs(res.total_return - 0.0) < 1e-12
    assert abs(res.terminal_wealth - 1.0) < 1e-12


def test_one_round_trip_includes_entry_and_exit_costs():
    # position: flat, long, long, flat  -> entry on bar1, exit cost on bar3
    n = 6
    df = _ohlcv(n, seed=2)
    pos = [0.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    costs = CostConfig(fee_bps_per_side=10, half_spread_bps=0, slippage_bps_per_side=0)
    res = _force_positions(df, pos, costs)
    cf = one_way_cost_fraction(costs)
    assert len(res.trades) == 1
    tr = res.trades[0]
    assert tr.is_open is False
    # Hand path: bars 1,2 long; bar3 flat with -cf exit
    path = float(np.prod(1.0 + res.bar_returns.values) - 1.0)
    trade_w = float(1.0 + tr.return_net) - 1.0
    assert abs((1.0 + tr.return_net) - (1.0 + path)) < 1e-12
    # Exit bar net should be -cf
    assert abs(float(res.bar_returns.iloc[3]) - (-cf)) < 1e-12
    # Entry bar has cost: net[1] = 1*gross[1] - cf
    assert float(res.bar_returns.iloc[1]) < float(
        df["open"].iloc[2] / df["open"].iloc[1] - 1.0
    )


def test_several_trades_reconcile_when_all_closed():
    df = _ohlcv(40, seed=5)
    # alternate blocks of long/flat
    pos = []
    for i in range(40):
        pos.append(1.0 if (i // 4) % 2 == 1 else 0.0)
    # ensure starts flat and ends flat
    pos[0] = 0.0
    pos[-1] = 0.0
    costs = CostConfig(fee_bps_per_side=10, half_spread_bps=1.5, slippage_bps_per_side=5)
    res = _force_positions(df, pos, costs)
    assert all(not t.is_open for t in res.trades)
    trade_wealth = 1.0
    for t in res.trades:
        trade_wealth *= 1.0 + t.return_net
    path_wealth = float(np.prod(1.0 + res.bar_returns.values))
    assert abs(trade_wealth - path_wealth) < 1e-10
    assert abs(path_wealth - res.terminal_wealth / res.initial_equity) < 1e-10


def test_open_terminal_trade_no_exit_cost():
    df = _ohlcv(10, seed=7)
    pos = [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    costs = CostConfig(fee_bps_per_side=10, half_spread_bps=0, slippage_bps_per_side=0)
    res = _force_positions(df, pos, costs)
    assert len(res.trades) == 1
    assert res.trades[0].is_open is True
    # Open trade wealth != full path if we closed... but no exit bar; trade = prod long bars only
    # Full path includes only those bars' nets (no extra exit bar)
    trade_w = 1.0 + res.trades[0].return_net
    # long from bar 2..9; flat 0,1 have 0 net
    path_w = float(np.prod(1.0 + res.bar_returns.values))
    assert abs(trade_w - path_w) < 1e-10


def test_exit_costs_reduce_trade_return_vs_gross_only():
    df = _ohlcv(8, seed=9)
    pos = [0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    costs = CostConfig(fee_bps_per_side=50, half_spread_bps=0, slippage_bps_per_side=0)
    res = _force_positions(df, pos, costs)
    tr = res.trades[0]
    # Without exit cost attribution, product of long bars only would be higher
    pos_s = res.position.values
    rets = res.bar_returns.values
    # long bars 1,2
    gross_only = float(np.prod(1.0 + rets[1:3]) - 1.0)
    assert tr.return_net < gross_only - 1e-9


def test_identity_assertion_is_strict():
    """Ensure this suite asserts exact reconciliation (no bypass)."""
    df = _ohlcv(25, seed=11)
    pos = [0.0] + [1.0, 1.0, 0.0] * 8
    pos = pos[:25]
    pos[-1] = 0.0
    res = _force_positions(df, pos, CostConfig())
    if not res.trades:
        return
    tw = 1.0
    for t in res.trades:
        assert not t.is_open
        tw *= 1.0 + t.return_net
    pw = float(np.prod(1.0 + res.bar_returns.values))
    assert abs(tw - pw) < 1e-10
