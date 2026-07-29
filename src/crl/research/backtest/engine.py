"""Long-only bar backtest with reconciled trade and equity paths.

Execution model (Phase 1 locked):
- Features/rules use data available at close of bar t only.
- Desired position is set at close t.
- Position for bar t+1 = desired[t] (lag-1).
- Gross return while long: open[t] → open[t+1] (last bar: open→close).
- One-way costs charged on |Δposition| at the bar where position changes.
- Entry cost sits on the first long bar; exit cost sits on the first flat bar
  after a long segment and is **attributed to that closed trade**.
- Initial equity is explicitly 1.0 (or caller-provided). Terminal wealth is
  initial_equity * prod_t(1 + r_net_t).

PnL identity (all positions closed by end):
  prod_j (1 + trade_j.return_net) == prod_t (1 + bar_net_t)
  == equity_T / initial_equity
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
    initial_equity: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def terminal_wealth(self) -> float:
        if self.equity.empty:
            return float(self.initial_equity)
        return float(self.equity.iloc[-1])

    @property
    def total_return(self) -> float:
        """Return from explicit initial capital (includes first bar)."""
        return self.terminal_wealth / float(self.initial_equity) - 1.0


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
    if "open" in df.columns:
        o = df["open"].astype(float)
        c = df["close"].astype(float)
        nxt = o.shift(-1)
        gross = nxt / o - 1.0
        gross.iloc[-1] = c.iloc[-1] / o.iloc[-1] - 1.0
        return gross.fillna(0.0), "open_to_next_open"
    c = df["close"].astype(float)
    return c.pct_change().fillna(0.0), "close_to_close_fallback"


def run_backtest_desired(
    df: pd.DataFrame,
    desired: pd.Series,
    costs: CostConfig,
    *,
    stress: bool = False,
    initial_equity: float = 1.0,
    meta: dict[str, Any] | None = None,
) -> BacktestResult:
    """Long-only backtest from an explicit desired-position series (lag-1 fill)."""
    if "close" not in df.columns:
        raise ValueError("df must include close")
    if initial_equity <= 0:
        raise ValueError("initial_equity must be positive")
    if len(desired) != len(df) or not desired.index.equals(df.index):
        desired = desired.reindex(df.index).fillna(0.0)
    desired = desired.astype(float).clip(0.0, 1.0)
    position = desired.shift(1).fillna(0.0)

    gross, fill_model = _bar_gross_returns(df)
    cost_frac = one_way_cost_fraction(costs, stress=stress)
    delta = position.diff().fillna(position.iloc[0])
    trade_cost = delta.abs() * cost_frac
    net = position * gross - trade_cost

    wealth = float(initial_equity)
    eq_vals = []
    for r in net.astype(float).values:
        wealth *= 1.0 + float(r)
        eq_vals.append(wealth)
    equity = pd.Series(eq_vals, index=df.index, name="equity")

    trades = _trades_from_bar_returns(df, position, net, cost_frac=cost_frac)
    out_meta: dict[str, Any] = {
        "stress": stress,
        "fill_model": fill_model,
        "pnl_identity": "closed_trades_include_entry_and_exit_costs",
        "cost_frac_one_way": cost_frac,
    }
    if meta:
        out_meta.update(meta)
    return BacktestResult(
        equity=equity,
        position=position.rename("position"),
        trades=trades,
        bar_returns=net.rename("bar_return"),
        signals=desired.rename("desired"),
        initial_equity=float(initial_equity),
        meta=out_meta,
    )


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
    if initial_equity <= 0:
        raise ValueError("initial_equity must be positive")

    desired = desired_position_from_rules(
        df, spec.entry.expression, spec.exit.expression
    )
    return run_backtest_desired(
        df,
        desired,
        costs,
        stress=stress,
        initial_equity=initial_equity,
        meta={"spec_id": spec.id},
    )


def _trades_from_bar_returns(
    df: pd.DataFrame,
    position: pd.Series,
    bar_net: pd.Series,
    *,
    cost_frac: float,
) -> list[Trade]:
    """Build trades with entry+exit costs in return_net for closed trades.

    Long segment on bars [start, end] inclusive (position > 0).
    - Entry cost is embedded in bar_net[start] (Δposition > 0 on that bar).
    - Exit cost is on bar end+1 when position drops to 0; that bar's net
      (typically -cost_frac) is multiplied into the closed trade.
    - Terminal open trade: no exit cost; is_open=True.
    """
    trades: list[Trade] = []
    regimes = (
        df["regime"] if "regime" in df.columns else pd.Series("unknown", index=df.index)
    )
    pos = position.values
    rets = bar_net.astype(float).values
    n = len(df)
    i = 0
    # Long segments: position strictly > 0.5. Position == 0.5 is treated as flat
    # so the scanner always advances (avoids infinite loop at exactly 0.5).
    while i < n:
        if pos[i] <= 0.5:
            i += 1
            continue
        start = i
        while i < n and pos[i] > 0.5:
            i += 1
        end = i - 1  # last long bar
        segment = rets[start : end + 1]
        factor = float(np.prod(1.0 + segment))

        is_open = end == n - 1 and pos[end] > 0.5
        # Closed if next bar exists and is flat (standard exit)
        if end + 1 < n and pos[end + 1] <= 0.5:
            is_open = False
            # Attribute exit-bar net (includes exit cost; gross*0 - cost)
            factor *= 1.0 + float(rets[end + 1])
            exit_time = df.index[end + 1]
            if "open" in df.columns:
                exit_px = float(df["open"].iloc[end + 1]) * (1.0 - cost_frac)
            else:
                exit_px = float(df["close"].iloc[end + 1]) * (1.0 - cost_frac)
        elif is_open:
            exit_time = df.index[end]
            if "open" in df.columns:
                exit_px = float(df["close"].iloc[end])  # MTM mark, no exit cost
            else:
                exit_px = float(df["close"].iloc[end])
        else:
            # end of series but flat? shouldn't happen if we entered long
            exit_time = df.index[end]
            exit_px = float(df["close"].iloc[end])

        ret_net = factor - 1.0
        if "open" in df.columns:
            entry_px = float(df["open"].iloc[start]) * (1.0 + cost_frac)
        else:
            entry_px = float(df["close"].iloc[start]) * (1.0 + cost_frac)

        trades.append(
            Trade(
                entry_time=df.index[start],
                exit_time=exit_time,
                entry_price=entry_px,
                exit_price=exit_px,
                return_net=ret_net,
                bars_held=end - start + 1,
                regime_at_entry=str(regimes.iloc[start]),
                is_open=is_open,
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
    """Always long; entry cost on first bar; no forced terminal exit cost."""
    gross, fill_model = _bar_gross_returns(df)
    cost_frac = one_way_cost_fraction(costs, stress=stress)
    net = gross.copy()
    net.iloc[0] = net.iloc[0] - cost_frac

    wealth = float(initial_equity)
    eq_vals = []
    for r in net.astype(float).values:
        wealth *= 1.0 + float(r)
        eq_vals.append(wealth)
    equity = pd.Series(eq_vals, index=df.index, name="equity")

    if "open" in df.columns:
        entry_px = float(df["open"].iloc[0]) * (1.0 + cost_frac)
    else:
        entry_px = float(df["close"].iloc[0]) * (1.0 + cost_frac)
    exit_px = float(df["close"].iloc[-1])
    trade = Trade(
        entry_time=df.index[0],
        exit_time=df.index[-1],
        entry_price=entry_px,
        exit_price=exit_px,
        return_net=float(equity.iloc[-1] / initial_equity - 1.0),
        bars_held=len(df),
        regime_at_entry=str(df["regime"].iloc[0]) if "regime" in df.columns else None,
        is_open=True,  # never paid exit cost (hold forever baseline)
    )
    return BacktestResult(
        equity=equity,
        position=pd.Series(1.0, index=df.index, name="position"),
        trades=[trade],
        bar_returns=net.rename("bar_return"),
        signals=pd.Series(1.0, index=df.index),
        initial_equity=float(initial_equity),
        meta={"baseline": "buy_and_hold", "fill_model": fill_model},
    )


def always_cash(df: pd.DataFrame, *, initial_equity: float = 1.0) -> BacktestResult:
    z = pd.Series(0.0, index=df.index)
    eq = pd.Series(float(initial_equity), index=df.index, name="equity")
    return BacktestResult(
        equity=eq,
        position=z.rename("position"),
        trades=[],
        bar_returns=z.rename("bar_return"),
        signals=z,
        initial_equity=float(initial_equity),
        meta={"baseline": "cash"},
    )


def sma_crossover_baseline(
    df: pd.DataFrame,
    costs: CostConfig,
    *,
    fast: int = 50,
    slow: int = 200,
    stress: bool = False,
    initial_equity: float = 1.0,
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
    return run_backtest(df, spec, costs, stress=stress, initial_equity=initial_equity)


def compounded_path_return(bar_returns: np.ndarray | pd.Series) -> float:
    r = np.asarray(bar_returns, dtype=float)
    if r.size == 0:
        return 0.0
    return float(np.prod(1.0 + r) - 1.0)
