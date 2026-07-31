"""Funding-carry research backtest (hedged-style approximation).

Authorized for research only (human 2026-07-31). Not a live trading path.
PnL is funding income when 'in carry', not directional spot alpha.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from crl.research.backtest.costs import one_way_cost_fraction as _one_way
from crl.research.backtest.engine import BacktestResult
from crl.shared.data.funding import validate_funding_events
from crl.shared.types import CostConfig, Trade


def one_way_cost_fraction(costs: CostConfig, *, stress: bool = False) -> float:
    # Carry flip touches spot + perp ≈ 2 legs
    return _one_way(costs, stress=stress) * 2.0


def daily_funding_income(
    bar_index: pd.DatetimeIndex,
    funding_events: pd.DataFrame,
) -> pd.Series:
    """Sum funding_rate for events with funding_time in (prev_close, bar_close].

    For daily bars labeled at midnight open, approximate bar day D as
    [D 00:00, D+1 00:00). Income on bar D is known by D+1 open → use shift
    when applying to positions (caller applies lag-1 on position).
    """
    ev = validate_funding_events(funding_events)
    bars = (
        bar_index.tz_convert("UTC")
        if bar_index.tz is not None
        else bar_index.tz_localize("UTC")
    )
    times = pd.DatetimeIndex(pd.to_datetime(ev["funding_time"], utc=True))
    rates = ev["funding_rate"].to_numpy(dtype=float)
    order = np.argsort(times.values)
    times = times[order]
    rates = rates[order]

    out = np.zeros(len(bars), dtype=float)
    j = 0
    n = len(times)
    for i, t0 in enumerate(bars):
        t0 = pd.Timestamp(t0).tz_convert("UTC")
        t1 = t0 + pd.Timedelta(days=1)
        while j < n and times[j] <= t0:
            j += 1
        k = j
        s = 0.0
        while k < n and times[k] < t1:
            s += float(rates[k])
            k += 1
        out[i] = s
    return pd.Series(out, index=bar_index, name="funding_income_1d")


def asof_funding_rate(bar_index: pd.DatetimeIndex, funding_events: pd.DataFrame) -> pd.Series:
    from crl.shared.data.funding import asof_funding_at_bar_close

    a = asof_funding_at_bar_close(bar_index, funding_events)
    return a["funding_last"]


@dataclass
class CarryRule:
    id: str
    description: str
    # function(frame) -> bool series desired in-carry
    kind: str
    threshold: float = 0.0


def desired_carry_mask(frame: pd.DataFrame, rule: CarryRule) -> pd.Series:
    fl = frame["funding_last"]
    inc = frame["funding_income_1d"]
    mu = fl.rolling(60, min_periods=30).mean()
    sd = fl.rolling(60, min_periods=30).std()
    z = (fl - mu) / sd.replace(0, np.nan)
    if rule.kind == "funding_last_pos":
        m = fl > rule.threshold
    elif rule.kind == "funding_last_high":
        # positive and above expanding median of positive era
        med = fl.expanding(min_periods=60).median()
        m = fl > med.clip(lower=0)
    elif rule.kind == "funding_z_pos":
        m = z > rule.threshold
    elif rule.kind == "funding_income_pos":
        m = inc > rule.threshold
    elif rule.kind == "always_carry":
        m = pd.Series(True, index=frame.index)
    else:
        raise ValueError(f"unknown rule kind {rule.kind}")
    return m.fillna(False)


def run_funding_carry_backtest(
    ohlcv: pd.DataFrame,
    funding_events: pd.DataFrame,
    rule: CarryRule,
    costs: CostConfig,
    *,
    residual_beta: float = 0.05,
    stress: bool = False,
    initial_equity: float = 1.0,
) -> BacktestResult:
    """Hedged carry approx: earn funding_income when in carry; residual haircut."""
    df = ohlcv.copy()
    df["funding_last"] = asof_funding_rate(df.index, funding_events)
    df["funding_income_1d"] = daily_funding_income(df.index, funding_events)
    # lag income one bar: today's printed funding sum applied after decision
    income = df["funding_income_1d"].shift(1).fillna(0.0)
    spot_ret = df["close"].pct_change().fillna(0.0)

    desired = desired_carry_mask(df, rule).astype(float)
    # lag-1 execution
    position = desired.shift(1).fillna(0.0)

    cost_frac = one_way_cost_fraction(costs, stress=stress)
    delta = position.diff().fillna(position.iloc[0])
    trade_cost = delta.abs() * cost_frac
    residual = residual_beta * spot_ret.abs() * position
    # When in carry, earn funding; residual risk haircut; costs on flips
    net = position * income - residual - trade_cost

    wealth = float(initial_equity)
    eq = []
    for r in net.astype(float).values:
        wealth *= 1.0 + float(r)
        eq.append(wealth)
    equity = pd.Series(eq, index=df.index, name="equity")

    trades = _carry_trades(position, net)
    return BacktestResult(
        equity=equity,
        position=position.rename("position"),
        trades=trades,
        bar_returns=net.rename("bar_return"),
        signals=desired.rename("desired"),
        initial_equity=float(initial_equity),
        meta={
            "model": "funding_carry_approx_v1",
            "rule_id": rule.id,
            "residual_beta": residual_beta,
            "stress": stress,
            "note": "Hedged research approximation; not live execution",
        },
    )


def _carry_trades(position: pd.Series, bar_net: pd.Series) -> list[Trade]:
    trades: list[Trade] = []
    pos = position.fillna(0.0).to_numpy()
    rets = bar_net.fillna(0.0).to_numpy()
    idx = position.index
    i = 0
    n = len(pos)
    while i < n:
        if pos[i] <= 0.5:
            i += 1
            continue
        start = i
        while i < n and pos[i] > 0.5:
            i += 1
        end = i - 1
        seg = rets[start : end + 1]
        # compound segment
        r_net = float(np.prod(1.0 + seg) - 1.0) if len(seg) else 0.0
        trades.append(
            Trade(
                entry_time=idx[start],
                exit_time=idx[end],
                entry_price=1.0,
                exit_price=1.0 + r_net,
                bars_held=end - start + 1,
                return_net=r_net,
                regime_at_entry="carry",
            )
        )
    return trades
