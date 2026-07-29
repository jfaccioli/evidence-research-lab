"""Platform execution engine — strategy → size → risk → lag-1 costs backtest.

Historical evaluation reuses research ``run_backtest_desired`` for PnL identity
with the lab cost model. Broker path available for paper/shadow integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import pandas as pd

from crl.platform.audit import AuditLog
from crl.platform.portfolio import PortfolioConfig, combine_single
from crl.platform.risk import PlatformRiskConfig, apply_risk_to_target
from crl.platform.sizing import SizingConfig, apply_sizing
from crl.platform.strategy import Strategy, StrategyMeta
from crl.research.backtest.engine import BacktestResult, run_backtest_desired
from crl.research.stats.metrics import compute_metrics
from crl.shared.types import CostConfig


@dataclass
class PlatformRunResult:
    strategy_meta: StrategyMeta
    desired: pd.Series
    sized: pd.Series
    risk_target: pd.Series
    backtest: BacktestResult
    metrics: dict[str, Any]
    audit_path: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_meta.id,
            "is_benchmark": self.strategy_meta.is_benchmark,
            "is_scientific_candidate": self.strategy_meta.is_scientific_candidate,
            "n_bars": len(self.desired),
            "long_frac": round(float(self.risk_target.mean()), 6),
            "metrics": self.metrics,
            "audit_path": self.audit_path,
            "scientific_claim": False if self.strategy_meta.is_benchmark else None,
            "note": (
                "Benchmark platform run — engineering validation only"
                if self.strategy_meta.is_benchmark
                else "Strategy run — promotion still requires confirmatory path"
            ),
            **self.meta,
        }


def run_platform_backtest(
    strategy: Strategy,
    ohlcv: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
    sizing: SizingConfig | None = None,
    portfolio: PortfolioConfig | None = None,
    risk: PlatformRiskConfig | None = None,
    initial_equity: float = 1.0,
    audit_dir: Path | None = None,
    context: dict[str, Any] | None = None,
) -> PlatformRunResult:
    """Full platform path on historical OHLCV (paper-sim costs)."""
    costs = costs or CostConfig()
    meta = strategy.meta
    if meta.is_benchmark is False and meta.is_scientific_candidate is False:
        raise RuntimeError("non-benchmark strategy must be scientific_candidate")

    run_id = uuid4().hex[:12]
    audit = AuditLog(
        run_id=run_id,
        strategy_id=meta.id,
        mode="historical_backtest",
        meta={"params": meta.params, "is_benchmark": meta.is_benchmark},
    )
    audit.add("start", n_bars=len(ohlcv))

    desired = strategy.desired_position(ohlcv, context=context)
    desired = desired.reindex(ohlcv.index).fillna(0.0).clip(0.0, 1.0)
    sized = apply_sizing(desired, sizing)
    port = combine_single(sized, portfolio)

    # Risk without equity first; optional second pass could use equity
    risk_target = apply_risk_to_target(port, equity=None, cfg=risk)

    bt = run_backtest_desired(
        ohlcv,
        risk_target,
        costs,
        initial_equity=initial_equity,
        meta={
            "platform": "1",
            "strategy_id": meta.id,
            "is_benchmark": meta.is_benchmark,
            "run_id": run_id,
        },
    )
    # Re-apply risk with equity path for daily-loss style halt (optional refine)
    risk2 = apply_risk_to_target(port, equity=bt.equity, cfg=risk)
    if not risk2.equals(risk_target):
        bt = run_backtest_desired(
            ohlcv,
            risk2,
            costs,
            initial_equity=initial_equity,
            meta={
                "platform": "1",
                "strategy_id": meta.id,
                "risk_refined": True,
                "run_id": run_id,
            },
        )
        risk_target = risk2

    metrics = compute_metrics(bt, timeframe="1d").model_dump()
    audit.add(
        "complete",
        n_trades=metrics.get("n_trades"),
        sharpe=metrics.get("sharpe_after_cost"),
        total_return=metrics.get("total_return"),
    )

    audit_path = None
    if audit_dir is not None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = Path(audit_dir) / f"platform_{meta.id}_{run_id}_{stamp}.json"
        audit.write(path)
        audit_path = str(path)

    return PlatformRunResult(
        strategy_meta=meta,
        desired=desired,
        sized=sized,
        risk_target=risk_target,
        backtest=bt,
        metrics=metrics,
        audit_path=audit_path,
        meta={"run_id": run_id, "costs": costs.model_dump()},
    )
