"""Long-only bar backtest with a single PnL identity.

Execution model (Phase 1 locked):
- Features/rules use data available at close of bar t only.
- Desired position is set at close t.
- Position for bar t+1 = desired[t] (lag-1).
- Bar gross return while long: open[t] → open[t+1] when available,
  else close-to-close (documented fallback).
- Costs charged once on position change (one-way bps × |Δposition|).
- Trade returns = sum of bar net returns over contiguous long segments
  (same series as equity path — no separate price-path fiction).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from crl.research.backtest.costs import one_way_cost_fraction
from crl.research.hypotheses.rules import eval_rule
from crl.shared.types import CostConfig, HypothesisSpec, Trade


@dataclass
class BacktestResult:
    equity: pd.Series
    position: pd.Series
    trades: list[Trade]
    bar_returns: pd.Series
    signals: pd.Series
    meta: dict[str, Any] = field(default_factory=dict)


def desired_position_from_rules(
    df: pd.DataFrame,
    entry_expr: str,
    exit_expr: str,
) -> pd.Series:
    """State machine on closed bars: 1=long desired, 0=flat."""
    pos = np.zeros(len(df), dtype=float)
    state = 0.0
    records = df.to_dict(orient="records")
    for i, row in enumerate(records):
        if state < 0.5:
            if eval_rule(entry_expr, row):
                state = 1.0
        else:
            if eval_rule(exit_expr, row):
                state = 0.0
        pos[i] = state
    return pd.Series(pos, index=df.index, name="desired_position")


def _bar_gross_returns(df: pd.DataFrame) -> tuple[pd.Series, str]:
    """Return per-bar gross returns and fill model label.

    Prefer open-to-open (aligned with next-open intention):
    r[t] = open[t+1]/open[t] - 1, shifted so r is earned while holding through bar t
    using position[t] decided before open[t]... 

    Cleaner identity used here:
    - position[t] held from open[t] to open[t+1]
    - gross[t] = open[t+1]/open[t] - 1  (last bar uses close/open)
    """
    if "open" in df.columns:
        o = df["open"].astype(float)
        c = df["close"].astype(float)
        # Return realized from open_t to open_{t+1}
        nxt = o.shift(-1)
        gross = nxt / o - 1.0
        # last bar: open → close
        gross.iloc[-1] = c.iloc[-1] / o.iloc[-1] - 1.0
        return gross.fillna(0.0), "open_to_next_open"
    c = df["close"].astype(float)
    return c.pct_change().fillna(0.0), "close_to_close_fallback"


def run_backtest(
    df: pd.DataFrame,
    spec: HypothesisSpec,
    costs: CostConfig,
    *,
    stress: bool = False,
    initial_equity: float = 1.0,
) -> BacktestResult:
    if "close" not in df.columns:
        raise ValueError("df must include close")

    desired = desired_position_from_rules(
        df, spec.entry.expression, spec.exit.expression
    )
    # Position held on bar t decided at close of t-1
    position = desired.shift(1).fillna(0.0)

    gross, fill_model = _bar_gross_returns(df)
    cost_frac = one_way_cost_fraction(costs, stress=stress)
    delta = position.diff().fillna(position.iloc[0])
    trade_cost = delta.abs() * cost_frac
    net = position * gross - trade_cost
    equity = (1.0 + net).cumprod() * initial_equity

    trades = _trades_from_bar_returns(df, position, net)
    return BacktestResult(
        equity=equity.rename("equity"),
        position=position.rename("position"),
        trades=trades,
        bar_returns=net.rename("bar_return"),
        signals=desired,
        meta={
            "stress": stress,
            "spec_id": spec.id,
            "fill_model": fill_model,
            "pnl_identity": "bar_net_sum_equals_trade_returns",
        },
    )


def _trades_from_bar_returns(
    df: pd.DataFrame,
    position: pd.Series,
    bar_net: pd.Series,
) -> list[Trade]:
    """Segment contiguous long periods; trade return = prod(1+r)-1 of bar nets."""
    trades: list[Trade] = []
    regimes = (
        df["regime"] if "regime" in df.columns else pd.Series("unknown", index=df.index)
    )
    pos = position.values
    rets = bar_net.astype(float).values
    n = len(df)
    i = 0
    while i < n:
        if pos[i] < 0.5:
            i += 1
            continue
        start = i
        while i < n and pos[i] > 0.5:
            i += 1
        end = i - 1  # inclusive last long bar
        segment = rets[start : end + 1]
        ret_net = float(np.prod(1.0 + segment) - 1.0)
        # Mark prices for reporting only (not a second PnL path)
        if "open" in df.columns:
            entry_px = float(df["open"].iloc[start])
            exit_px = (
                float(df["open"].iloc[end + 1])
                if end + 1 < n
                else float(df["close"].iloc[end])
            )
        else:
            entry_px = float(df["close"].iloc[start])
            exit_px = float(df["close"].iloc[end])
        trades.append(
            Trade(
                entry_time=df.index[start],
                exit_time=df.index[end],
                entry_price=entry_px,
                exit_price=exit_px,
                return_net=ret_net,
                bars_held=end - start + 1,
                regime_at_entry=str(regimes.iloc[start]),
            )
        )
    return trades


def buy_and_hold(
    df: pd.DataFrame,
    costs: CostConfig,
    *,
    stress: bool = False,
    initial_equity: float = 1.0,
) -> BacktestResult:
    gross, fill_model = _bar_gross_returns(df)
    cost_frac = one_way_cost_fraction(costs, stress=stress)
    net = gross.copy()
    # entry cost on first bar, no exit cost (hold forever baseline)
    net.iloc[0] = net.iloc[0] - cost_frac
    equity = (1.0 + net).cumprod() * initial_equity
    trades = _trades_from_bar_returns(
        df, pd.Series(1.0, index=df.index), net
    )
    # Override: single trade for B&H reporting
    if trades:
        trades = [
            Trade(
                entry_time=df.index[0],
                exit_time=df.index[-1],
                entry_price=trades[0].entry_price,
                exit_price=trades[-1].exit_price if trades else trades[0].exit_price,
                return_net=float(equity.iloc[-1] / equity.iloc[0] - 1.0),
                bars_held=len(df),
                regime_at_entry=str(df["regime"].iloc[0]) if "regime" in df.columns else None,
            )
        ]
    return BacktestResult(
        equity=equity.rename("equity"),
        position=pd.Series(1.0, index=df.index, name="position"),
        trades=trades,
        bar_returns=net.rename("bar_return"),
        signals=pd.Series(1.0, index=df.index),
        meta={"baseline": "buy_and_hold", "fill_model": fill_model},
    )


def always_cash(df: pd.DataFrame) -> BacktestResult:
    z = pd.Series(0.0, index=df.index)
    one = pd.Series(1.0, index=df.index)
    return BacktestResult(
        equity=one.rename("equity"),
        position=z.rename("position"),
        trades=[],
        bar_returns=z.rename("bar_return"),
        signals=z,
        meta={"baseline": "cash"},
    )


def sma_crossover_baseline(
    df: pd.DataFrame,
    costs: CostConfig,
    *,
    fast: int = 50,
    slow: int = 200,
    stress: bool = False,
) -> BacktestResult:
    from crl.shared.types import HypothesisSpec, RuleSpec, Taxonomy

    fcol, scol = f"sma_{fast}", f"sma_{slow}"
    if fcol not in df.columns or scol not in df.columns:
        raise ValueError(f"Need {fcol} and {scol} in features")
    spec = HypothesisSpec(
        id="baseline_sma_x",
        taxonomy=Taxonomy.TREND,
        entry=RuleSpec(expression=f"{fcol} > {scol}"),
        exit=RuleSpec(expression=f"{fcol} < {scol}"),
        rationale="Baseline SMA crossover",
    )
    return run_backtest(df, spec, costs, stress=stress)
