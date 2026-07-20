"""Performance metrics after costs.

Total return definition (C5 / P0):
  R = W_T / W_0 - 1
  where W_0 = initial_equity (default 1.0) and
  W_T = W_0 * prod_t (1 + r_net_t) = equity series terminal value.
  The first bar is included (no equity[0]-relative omission).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.backtest.engine import BacktestResult
from crl.shared.types import Metrics, Trade


def _ann_factor(timeframe: str, cfg_ann: dict | None = None) -> float:
    cfg_ann = cfg_ann or {}
    if timeframe in ("1d", "1D", "d"):
        return float(cfg_ann.get("annualization_1d", 365))
    if timeframe in ("4h", "4H"):
        return float(cfg_ann.get("annualization_4h", 2190))
    return 365.0


def max_drawdown(equity: pd.Series, *, initial_equity: float = 1.0) -> tuple[float, float]:
    """Max drawdown from a path that includes an explicit initial wealth point."""
    if equity.empty:
        return 0.0, 0.0
    # Prepend W_0 so first-bar losses count in DD
    path = pd.concat(
        [pd.Series([float(initial_equity)], index=[equity.index[0]]), equity]
    )
    # fix index uniqueness for first point
    path = pd.Series(
        [float(initial_equity)] + list(equity.astype(float).values),
        dtype=float,
    )
    peak = path.cummax()
    dd = path / peak - 1.0
    max_dd = float(dd.min()) if len(dd) else 0.0
    underwater = dd < 0
    frac = float(underwater.mean()) if len(underwater) else 0.0
    return abs(max_dd), frac


def compute_metrics(
    result: BacktestResult,
    *,
    timeframe: str = "1d",
    bh_result: BacktestResult | None = None,
    ann: dict | None = None,
) -> Metrics:
    rets = result.bar_returns.dropna()
    n = len(rets)
    af = _ann_factor(timeframe, ann)
    w0 = float(getattr(result, "initial_equity", 1.0) or 1.0)
    # C5: full-path return from initial capital (includes first bar)
    if hasattr(result, "total_return"):
        total_return = float(result.total_return)
    elif len(result.equity):
        total_return = float(result.equity.iloc[-1] / w0 - 1.0)
    else:
        total_return = 0.0

    years = n / af if af else 0.0
    cagr = (
        float((1.0 + total_return) ** (1.0 / years) - 1.0)
        if years > 0 and total_return > -1
        else 0.0
    )
    vol = float(rets.std(ddof=1) * np.sqrt(af)) if n > 2 else 0.0
    mean = float(rets.mean()) if n else 0.0
    # Annualized Sharpe: (mean * af) / (std * sqrt(af)) = mean/std * sqrt(af)
    sharpe = float((mean * af) / vol) if vol > 1e-12 else 0.0
    downside = rets[rets < 0]
    dvol = float(downside.std(ddof=1) * np.sqrt(af)) if len(downside) > 2 else 0.0
    sortino = float((mean * af) / dvol) if dvol > 1e-12 else 0.0
    mdd, uw = max_drawdown(result.equity, initial_equity=w0)
    calmar = float(cagr / mdd) if mdd > 1e-12 else 0.0

    trades = result.trades
    n_trades = len(trades)
    avg_tr = float(np.mean([t.return_net for t in trades])) if trades else 0.0
    avg_hold = float(np.mean([t.bars_held for t in trades])) if trades else 0.0
    edge_bps = avg_tr * 10_000 if trades else 0.0
    turnover = float(result.position.diff().abs().sum())

    excess = 0.0
    ir = 0.0
    beta = 0.0
    if bh_result is not None and len(bh_result.bar_returns) == len(rets):
        active = rets.values - bh_result.bar_returns.reindex(rets.index).fillna(0).values
        bh_w0 = float(getattr(bh_result, "initial_equity", 1.0) or 1.0)
        bh_total = (
            float(bh_result.total_return)
            if hasattr(bh_result, "total_return")
            else float(bh_result.equity.iloc[-1] / bh_w0 - 1.0)
        )
        excess = total_return - bh_total
        act = pd.Series(active)
        ir_den = float(act.std(ddof=1) * np.sqrt(af)) if len(act) > 2 else 0.0
        ir = float(act.mean() * af / ir_den) if ir_den > 1e-12 else 0.0
        bh = bh_result.bar_returns.reindex(rets.index).fillna(0).values
        if np.var(bh) > 1e-16:
            beta = float(np.cov(rets.values, bh)[0, 1] / np.var(bh))

    return Metrics(
        n_bars=n,
        n_trades=n_trades,
        total_return=total_return,
        cagr=cagr,
        volatility=vol,
        sharpe_after_cost=sharpe,
        sortino=sortino,
        calmar=calmar,
        max_drawdown=mdd,
        time_underwater_frac=uw,
        turnover=turnover,
        avg_trade_return=avg_tr,
        avg_hold_bars=avg_hold,
        edge_bps_per_trade=edge_bps,
        excess_return_vs_bh=excess,
        ir_vs_bh=ir,
        beta_proxy=beta,
    )


def trade_returns(trades: list[Trade]) -> np.ndarray:
    return np.array([t.return_net for t in trades], dtype=float)
