"""PCS_VOL_SCALE_V1 — inverse-vol continuous long sizing (pre-registered)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.research.backtest.engine import buy_and_hold, run_backtest_desired
from crl.research.backtest.splitter import chronological_split
from crl.research.stats.metrics import compute_metrics
from crl.shared.types import CostConfig, GateConfig, SplitConfig

FAMILY_ID = "pcs_vol_scale_v1"
PROGRAMME = "PCS_VOL_SCALE_V1"
PRIMARY_L = 20
ABLATION_LS = (15, 30)


def _rv(close: pd.Series, window: int) -> pd.Series:
    lr = np.log(close.astype(float) / close.astype(float).shift(1))
    return lr.rolling(window, min_periods=window).std()


def desired_inv_vol(
    ohlcv: pd.DataFrame,
    *,
    rv_window: int = PRIMARY_L,
    expand_min: int = 60,
    price_col: str = "close",
) -> pd.Series:
    """w = clip(expanding_median(rv_lag) / rv_lag, 0, 1), causal."""
    close = ohlcv[price_col].astype(float)
    rv_lag = _rv(close, rv_window).shift(1)
    med = rv_lag.expanding(min_periods=expand_min).median()
    ratio = med / rv_lag.replace(0.0, np.nan)
    return ratio.clip(0.0, 1.0).fillna(0.0).rename("desired")


def _rebalance_events(desired: pd.Series, thr: float = 0.05) -> int:
    d = desired.fillna(0.0).astype(float)
    return int((d.diff().abs() >= thr).sum())


def _metrics_pair(
    ohlcv: pd.DataFrame,
    desired: pd.Series,
    costs: CostConfig,
    *,
    stress: bool,
) -> tuple[dict[str, float], dict[str, float]]:
    des = desired.reindex(ohlcv.index).fillna(0.0)
    bt = run_backtest_desired(ohlcv, des, costs, stress=stress)
    bh = buy_and_hold(ohlcv, costs, stress=stress)
    m = compute_metrics(bt, timeframe="1d", bh_result=bh)
    mb = compute_metrics(bh, timeframe="1d")
    return (
        {
            "n_bars": float(m.n_bars),
            "n_trades": float(m.n_trades),
            "n_rebalances_d05": float(_rebalance_events(des)),
            "total_return": float(m.total_return),
            "sharpe_after_cost": float(m.sharpe_after_cost),
            "max_drawdown": float(m.max_drawdown),
            "turnover": float(m.turnover),
            "long_frac_mean_w": float(des.mean()),
            "excess_return_vs_bh": float(m.excess_return_vs_bh),
        },
        {
            "bh_sharpe": float(mb.sharpe_after_cost),
            "bh_max_dd": float(mb.max_drawdown),
            "bh_total_return": float(mb.total_return),
        },
    )


def evaluate_pcs_vol_scale(
    ohlcv: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
    splits: SplitConfig | None = None,
    gates: GateConfig | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """Pre-registered PCS_VOL_SCALE evaluation. Pass/fail on test, L=20 only."""
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
    assert costs is not None and splits is not None and gates is not None

    hold = chronological_split(ohlcv, splits)
    des_primary = desired_inv_vol(ohlcv, rv_window=PRIMARY_L)

    slices: dict[str, Any] = {}
    for name, frame in (
        ("train", hold.train),
        ("val", hold.val),
        ("test", hold.test),
    ):
        sm, bh = _metrics_pair(frame, des_primary, costs, stress=False)
        slices[name] = {**sm, **bh, "label": name, "stress": False}

    sm_s, bh_s = _metrics_pair(hold.test, des_primary, costs, stress=True)
    slices["test_stress"] = {**sm_s, **bh_s, "label": "test_stress", "stress": True}

    # half baseline on test only
    half_des = pd.Series(0.5, index=hold.test.index)
    half_m, _ = _metrics_pair(hold.test, half_des, costs, stress=False)
    slices["test"]["half_sharpe"] = half_m["sharpe_after_cost"]
    slices["test"]["half_max_dd"] = half_m["max_drawdown"]

    ablations: dict[str, Any] = {}
    for L in ABLATION_LS:
        dL = desired_inv_vol(ohlcv, rv_window=L)
        sm, bh = _metrics_pair(hold.test, dL, costs, stress=False)
        ablations[f"L{L}_test"] = {**sm, **bh, "label": f"ablation_L{L}"}

    test = slices["test"]
    train = slices["train"]
    stress = slices["test_stress"]
    bh_sharpe = test["bh_sharpe"]
    bh_dd = test["bh_max_dd"]

    activity_ok = (test["n_trades"] >= gates.min_trades) or (
        test["n_rebalances_d05"] >= gates.min_trades
    )
    checks = {
        "test_sharpe_ge_min": bool(test["sharpe_after_cost"] >= gates.sharpe_min),
        "test_max_dd_le_cap": bool(test["max_drawdown"] <= gates.max_drawdown),
        "activity_ok": bool(activity_ok),
        "not_worse_than_bh_on_both": bool(
            test["sharpe_after_cost"] >= bh_sharpe - 0.05
            and test["max_drawdown"] <= bh_dd + 1e-12
        ),
        "improves_bh_sharpe_or_dd": bool(
            test["sharpe_after_cost"] > bh_sharpe + 1e-9
            or test["max_drawdown"] < bh_dd - 1e-9
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
    abl_sharpes = [ablations[k]["sharpe_after_cost"] for k in ablations]
    checks["ablation_not_single_peak"] = not (
        test["sharpe_after_cost"] > 0.5 and all(s < 0 for s in abl_sharpes)
    )

    hard_keys = [
        "test_sharpe_ge_min",
        "test_max_dd_le_cap",
        "activity_ok",
        "not_worse_than_bh_on_both",
        "improves_bh_sharpe_or_dd",
        "stress_ok",
        "overfit_gap_ok",
        "ablation_not_single_peak",
    ]
    passed = bool(all(checks[k] for k in hard_keys))

    # round for JSON
    def _round_dict(d: dict[str, Any]) -> dict[str, Any]:
        out = {}
        for k, v in d.items():
            if isinstance(v, float):
                out[k] = round(v, 6)
            else:
                out[k] = v
        return out

    return {
        "programme": PROGRAMME,
        "family_id": FAMILY_ID,
        "mechanism": "inverse_vol_continuous_long_sizing",
        "primary_rv_window": PRIMARY_L,
        "slices": {k: _round_dict(v) for k, v in slices.items()},
        "ablations": {k: _round_dict(v) for k, v in ablations.items()},
        "gate_checks": checks,
        "confirmatory_pass": passed,
        "outcome": "A_shadow_eligible" if passed else "C_rejected",
        "promotion": (
            "eligible_for_shadow_package_prep"
            if passed
            else "rejected — retire pcs_vol_scale_v1"
        ),
        "note": (
            "Pass enables live-data shadow prep only; not APPROVED production alpha. "
            "Micro-live requires shadow acceptance + human capital approval."
        ),
    }
