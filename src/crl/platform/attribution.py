"""Simple performance attribution vs buy-and-hold (engineering)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from crl.platform.engine import run_platform_backtest
from crl.platform.strategy import Strategy, get_strategy
from crl.research.backtest.engine import buy_and_hold
from crl.research.stats.metrics import compute_metrics
from crl.shared.types import CostConfig


def attribute_vs_buy_and_hold(
    strategy: Strategy,
    ohlcv: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
) -> dict[str, Any]:
    """Compare strategy metrics to buy-and-hold on same sample."""
    costs = costs or CostConfig()
    run = run_platform_backtest(strategy, ohlcv, costs=costs)
    bh = buy_and_hold(ohlcv, costs)
    m_s = compute_metrics(run.backtest, timeframe="1d", bh_result=bh)
    m_b = compute_metrics(bh, timeframe="1d")
    return {
        "strategy_id": strategy.meta.id,
        "is_benchmark": strategy.meta.is_benchmark,
        "strategy": {
            "total_return": round(m_s.total_return, 6),
            "sharpe_after_cost": round(m_s.sharpe_after_cost, 6),
            "max_drawdown": round(m_s.max_drawdown, 6),
            "n_trades": m_s.n_trades,
            "excess_return_vs_bh": round(m_s.excess_return_vs_bh, 6),
        },
        "buy_and_hold": {
            "total_return": round(m_b.total_return, 6),
            "sharpe_after_cost": round(m_b.sharpe_after_cost, 6),
            "max_drawdown": round(m_b.max_drawdown, 6),
        },
        "note": "Attribution for platform validation — not a science claim",
    }


def attribute_all_benchmarks(
    ohlcv: pd.DataFrame, *, costs: CostConfig | None = None
) -> dict[str, Any]:
    from crl.platform.benchmarks import all_benchmark_ids

    rows = []
    for sid in all_benchmark_ids():
        rows.append(attribute_vs_buy_and_hold(get_strategy(sid), ohlcv, costs=costs))
    return {
        "n": len(rows),
        "benchmarks": rows,
        "scientific_promotion": "not_applicable",
    }
