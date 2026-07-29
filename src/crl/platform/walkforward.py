"""Walk-forward evaluation for platform strategies (engineering harness)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from crl.platform.engine import run_platform_backtest
from crl.platform.strategy import Strategy
from crl.research.backtest.splitter import walk_forward_folds
from crl.shared.types import CostConfig, SplitConfig


def walkforward_strategy(
    strategy: Strategy,
    ohlcv: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
    splits: SplitConfig | None = None,
) -> dict[str, Any]:
    """Run strategy on each WF validation fold; report fold Sharpes.

    Benchmarks only for platform validation — not science promotion.
    """
    costs = costs or CostConfig()
    splits = splits or SplitConfig()
    folds = walk_forward_folds(ohlcv, splits)
    rows = []
    for fold in folds:
        # Need enough history for SMA200 etc. — use train+val for warm start signals
        # but evaluate metrics on val only
        combo = pd.concat([fold.train, fold.val])
        if len(combo) < 50:
            continue
        res = run_platform_backtest(strategy, combo, costs=costs)
        from crl.research.backtest.engine import run_backtest_desired
        from crl.research.stats.metrics import compute_metrics

        des_val = res.desired.reindex(fold.val.index).fillna(0.0)
        bt_val = run_backtest_desired(
            fold.val,
            des_val,
            costs,
            meta={"fold": fold.fold_id, "strategy": strategy.meta.id},
        )
        m = compute_metrics(bt_val, timeframe="1d")
        rows.append(
            {
                "fold_id": fold.fold_id,
                "n_val": len(fold.val),
                "sharpe_after_cost": round(m.sharpe_after_cost, 6),
                "total_return": round(m.total_return, 6),
                "n_trades": m.n_trades,
                "long_frac": round(float(des_val.mean()), 6),
            }
        )

    sharpes = [r["sharpe_after_cost"] for r in rows if r["n_val"] > 10]
    pos_frac = (
        sum(1 for s in sharpes if s > 0) / len(sharpes) if sharpes else None
    )
    return {
        "strategy_id": strategy.meta.id,
        "is_benchmark": strategy.meta.is_benchmark,
        "n_folds": len(rows),
        "positive_sharpe_fold_frac": round(pos_frac, 4) if pos_frac is not None else None,
        "folds": rows,
        "note": "Walk-forward platform harness — not a confirmatory science result",
        "scientific_promotion": "not_applicable",
    }
