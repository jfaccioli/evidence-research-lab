"""PCS_BASIS_RISKOFF_V1 — flat when |basis| high, else long."""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.research.backtest.engine import buy_and_hold, run_backtest_desired
from crl.research.backtest.splitter import chronological_split
from crl.research.market_properties.cross_venue_basis import align_basis_to_ohlcv
from crl.research.stats.metrics import compute_metrics
from crl.shared.types import CostConfig, GateConfig, SplitConfig

FAMILY_ID = "pcs_basis_riskoff_v1"
PROGRAMME = "PCS_BASIS_RISKOFF_V1"


def desired_basis_riskoff(
    ohlcv: pd.DataFrame,
    basis_events: pd.DataFrame,
    *,
    expand_min: int = 60,
    q: float = 0.90,
) -> pd.Series:
    fr = align_basis_to_ohlcv(ohlcv, basis_events)
    ab = fr["basis"].abs()
    thr = ab.expanding(min_periods=expand_min).quantile(q)
    # lag for decision
    ab_lag = ab.shift(1)
    thr_lag = thr.shift(1)
    w = (ab_lag < thr_lag).astype(float)
    return w.fillna(0.0).rename("desired")


def evaluate_pcs_basis_riskoff(
    ohlcv: pd.DataFrame,
    basis_events: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
    splits: SplitConfig | None = None,
    gates: GateConfig | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    if costs is None or splits is None or gates is None:
        from crl.shared.config import (
            cost_from_config,
            gates_from_config,
            load_config,
            splits_from_config,
        )

        cfg = load_config(config_path)
        costs = costs or cost_from_config(cfg)
        splits = splits or splits_from_config(cfg)
        gates = gates or gates_from_config(cfg)
    assert costs and splits and gates

    hold = chronological_split(ohlcv, splits)
    des = desired_basis_riskoff(ohlcv, basis_events)

    def pack(frame: pd.DataFrame, stress: bool = False) -> dict[str, Any]:
        d = des.reindex(frame.index).fillna(0.0)
        bt = run_backtest_desired(frame, d, costs, stress=stress)
        bh = buy_and_hold(frame, costs, stress=stress)
        m = compute_metrics(bt, timeframe="1d", bh_result=bh)
        mb = compute_metrics(bh, timeframe="1d")
        return {
            "n_bars": m.n_bars,
            "n_trades": m.n_trades,
            "total_return": round(m.total_return, 6),
            "sharpe_after_cost": round(m.sharpe_after_cost, 6),
            "max_drawdown": round(m.max_drawdown, 6),
            "long_frac": round(float(d.mean()), 6),
            "bh_sharpe": round(mb.sharpe_after_cost, 6),
            "bh_max_dd": round(mb.max_drawdown, 6),
            "bh_total_return": round(mb.total_return, 6),
            "excess_return_vs_bh": round(m.excess_return_vs_bh, 6),
            "stress": stress,
        }

    slices = {
        "train": pack(hold.train),
        "val": pack(hold.val),
        "test": pack(hold.test),
        "test_stress": pack(hold.test, stress=True),
    }
    test, train, stress = slices["test"], slices["train"], slices["test_stress"]
    checks = {
        "test_sharpe_ge_min": bool(test["sharpe_after_cost"] >= gates.sharpe_min),
        "test_max_dd_le_cap": bool(test["max_drawdown"] <= gates.max_drawdown),
        "activity_ok": bool(test["n_trades"] >= 15),
        "not_worse_than_bh_on_both": bool(
            test["sharpe_after_cost"] >= test["bh_sharpe"] - 0.05
            and test["max_drawdown"] <= test["bh_max_dd"] + 1e-12
        ),
        "improves_bh_sharpe_or_dd": bool(
            test["sharpe_after_cost"] > test["bh_sharpe"] + 1e-9
            or test["max_drawdown"] < test["bh_max_dd"] - 1e-9
        ),
        "stress_ok": bool(
            stress["sharpe_after_cost"] >= 0.0
            or stress["max_drawdown"] <= stress["bh_max_dd"] + 1e-12
        ),
        "overfit_gap_ok": bool(
            abs(train["sharpe_after_cost"] - test["sharpe_after_cost"])
            <= gates.overfit_gap_max
        ),
    }
    passed = bool(all(checks.values()))
    return {
        "programme": PROGRAMME,
        "family_id": FAMILY_ID,
        "mechanism": "dislocation_abs_basis_risk_off",
        "slices": slices,
        "gate_checks": checks,
        "confirmatory_pass": passed,
        "outcome": "A_shadow_eligible" if passed else "C_rejected",
        "promotion": (
            "eligible_for_shadow_package_prep"
            if passed
            else "rejected — retire pcs_basis_riskoff_v1"
        ),
    }
