"""LEDA-4/5b: full-stack and risk-policy economic evaluation.

Exploratory only. Does **not** register confirmatory trials or claim APPROVED.
Uses the same lag-1 next_open cost model as the research engine.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.leda.channels.trend import build_trend_evidence
from crl.leda.channels.vol_risk import build_vol_risk_evidence
from crl.research.backtest.engine import buy_and_hold, run_backtest_desired
from crl.research.backtest.splitter import chronological_split
from crl.research.stats.metrics import compute_metrics
from crl.shared.config import cost_from_config, gates_from_config, load_config, splits_from_config
from crl.shared.types import CostConfig, GateConfig, SplitConfig


def desired_from_leda_scores(
    e_forecast: pd.Series,
    e_risk: pd.Series,
    *,
    forecast_long_threshold: float = 0.5,
    risk_veto_threshold: float = 0.85,
) -> pd.Series:
    """Stateless thin map: long iff forecast high and risk not vetoed.

    Missing forecast → flat. Missing risk → no veto (channel not warm).
    """
    f = e_forecast.astype(float)
    r = e_risk.astype(float)
    want = f >= forecast_long_threshold
    veto = r.notna() & (r >= risk_veto_threshold)
    want = want & f.notna()
    desired = (want & ~veto).astype(float)
    return desired.reindex(e_forecast.index).fillna(0.0)


def desired_bh_with_vol_veto(
    e_risk: pd.Series,
    *,
    risk_veto_threshold: float = 0.85,
) -> pd.Series:
    """Always-long except risk veto (LEDA-5b). No directional forecast claim."""
    r = e_risk.astype(float)
    veto = r.notna() & (r >= risk_veto_threshold)
    # Long when not vetoed; missing risk → long (B&H until risk channel warm)
    desired = (~veto).astype(float)
    return desired.reindex(e_risk.index).fillna(1.0)


def build_leda_desired(
    ohlcv: pd.DataFrame,
    *,
    forecast_long_threshold: float = 0.5,
    risk_veto_threshold: float = 0.85,
) -> tuple[pd.Series, pd.DataFrame]:
    """Build full-sample desired position from LEDA-1 + LEDA-2 channels."""
    trend = build_trend_evidence(ohlcv)
    vol = build_vol_risk_evidence(ohlcv)
    desired = desired_from_leda_scores(
        trend["score"],
        vol["score"],
        forecast_long_threshold=forecast_long_threshold,
        risk_veto_threshold=risk_veto_threshold,
    )
    aux = pd.DataFrame(
        {
            "e_forecast": trend["score"],
            "e_risk": vol["score"],
            "desired": desired,
        },
        index=ohlcv.index,
    )
    return desired, aux


def _slice_metrics(
    df: pd.DataFrame,
    desired: pd.Series,
    costs: CostConfig,
    *,
    timeframe: str = "1d",
    path_label: str = "stack",
) -> dict[str, Any]:
    d = desired.reindex(df.index).fillna(0.0)
    bt = run_backtest_desired(
        df,
        d,
        costs,
        meta={"leda": "econ", "path": path_label},
    )
    bh = buy_and_hold(df, costs)
    m = compute_metrics(bt, timeframe=timeframe, bh_result=bh)
    return {
        "n_bars": m.n_bars,
        "n_trades": m.n_trades,
        "total_return": round(m.total_return, 6),
        "cagr": round(m.cagr, 6),
        "sharpe_after_cost": round(m.sharpe_after_cost, 6),
        "max_drawdown": round(m.max_drawdown, 6),
        "time_underwater_frac": round(m.time_underwater_frac, 6),
        "excess_return_vs_bh": round(m.excess_return_vs_bh, 6),
        "bh_total_return": round(
            float(bh.total_return) if hasattr(bh, "total_return") else float("nan"),
            6,
        ),
        "long_frac": round(float(d.mean()), 6),
    }


def _gate_checklist(
    slices: dict[str, dict[str, Any]],
    gates: GateConfig,
) -> tuple[dict[str, bool], bool]:
    test = slices["test"]
    val = slices["val"]
    checklist = {
        "test_min_trades": bool(test["n_trades"] >= gates.min_trades),
        "test_sharpe_ge_min": bool(test["sharpe_after_cost"] >= gates.sharpe_min),
        "test_max_dd_le_cap": bool(test["max_drawdown"] <= gates.max_drawdown),
        "val_sharpe_finite": bool(np.isfinite(val["sharpe_after_cost"])),
    }
    gap = abs(slices["train"]["sharpe_after_cost"] - test["sharpe_after_cost"])
    checklist["overfit_gap_ok"] = bool(gap <= gates.overfit_gap_max)
    all_hard = bool(
        all(
            checklist[k]
            for k in (
                "test_min_trades",
                "test_sharpe_ge_min",
                "test_max_dd_le_cap",
                "overfit_gap_ok",
            )
        )
    )
    return checklist, all_hard


def evaluate_stack_economic(
    ohlcv: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
    splits: SplitConfig | None = None,
    gates: GateConfig | None = None,
    forecast_long_threshold: float = 0.5,
    risk_veto_threshold: float = 0.85,
    timeframe: str = "1d",
    config_path: str | None = None,
) -> dict[str, Any]:
    """Chronological train/val/test economic eval of thin LEDA stack (LEDA-4)."""
    cfg = load_config(config_path)
    costs = costs or cost_from_config(cfg)
    splits = splits or splits_from_config(cfg)
    gates = gates or gates_from_config(cfg)

    desired, aux = build_leda_desired(
        ohlcv,
        forecast_long_threshold=forecast_long_threshold,
        risk_veto_threshold=risk_veto_threshold,
    )
    hold = chronological_split(ohlcv.copy(), splits)
    slices = {
        "train": _slice_metrics(hold.train, desired, costs, timeframe=timeframe),
        "val": _slice_metrics(hold.val, desired, costs, timeframe=timeframe),
        "test": _slice_metrics(hold.test, desired, costs, timeframe=timeframe),
    }
    checklist, all_hard = _gate_checklist(slices, gates)

    return {
        "leda": "4",
        "mode": "exploratory",
        "promotion": "not_approved — LEDA-4 is diagnostic full-stack economics only",
        "channel_ids": ["leda2_trend", "leda1_vol_risk"],
        "map": {
            "want_long": f"e_forecast >= {forecast_long_threshold}",
            "veto": f"e_risk >= {risk_veto_threshold}",
            "portfolio": "unit long-only",
            "execution": "next_open lag-1",
        },
        "n_bars": len(ohlcv),
        "n_scored_forecast": int(aux["e_forecast"].notna().sum()),
        "n_scored_risk": int(aux["e_risk"].notna().sum()),
        "full_sample_long_frac": round(float(desired.mean()), 6),
        "slices": slices,
        "gate_checklist_test": checklist,
        "exploratory_hard_gates_pass": all_hard,
        "note": (
            "Hard-gate checklist is a diagnostic under frozen thresholds; "
            "passing does not grant APPROVED or open shadow without director review"
        ),
    }


def evaluate_vol_veto_policy(
    ohlcv: pd.DataFrame,
    *,
    costs: CostConfig | None = None,
    splits: SplitConfig | None = None,
    gates: GateConfig | None = None,
    risk_veto_threshold: float = 0.85,
    timeframe: str = "1d",
    config_path: str | None = None,
) -> dict[str, Any]:
    """LEDA-5b: always-long with vol risk veto only (no forecast alpha claim)."""
    cfg = load_config(config_path)
    costs = costs or cost_from_config(cfg)
    splits = splits or splits_from_config(cfg)
    gates = gates or gates_from_config(cfg)

    vol = build_vol_risk_evidence(ohlcv)
    desired = desired_bh_with_vol_veto(
        vol["score"], risk_veto_threshold=risk_veto_threshold
    )
    hold = chronological_split(ohlcv.copy(), splits)
    slices = {
        "train": _slice_metrics(
            hold.train, desired, costs, timeframe=timeframe, path_label="vol_veto_bh"
        ),
        "val": _slice_metrics(
            hold.val, desired, costs, timeframe=timeframe, path_label="vol_veto_bh"
        ),
        "test": _slice_metrics(
            hold.test, desired, costs, timeframe=timeframe, path_label="vol_veto_bh"
        ),
    }
    checklist, all_hard = _gate_checklist(slices, gates)

    return {
        "leda": "5b",
        "mode": "exploratory",
        "promotion": "not_approved — risk-policy diagnostic only",
        "channel_ids": ["leda1_vol_risk"],
        "map": {
            "want_long": "always (B&H baseline)",
            "veto": f"e_risk >= {risk_veto_threshold}",
            "portfolio": "unit long-only",
            "execution": "next_open lag-1",
        },
        "n_bars": len(ohlcv),
        "n_scored_risk": int(vol["score"].notna().sum()),
        "full_sample_long_frac": round(float(desired.mean()), 6),
        "slices": slices,
        "gate_checklist_test": checklist,
        "exploratory_hard_gates_pass": all_hard,
        "note": (
            "Tests whether vol-risk veto improves B&H economics; "
            "not directional alpha; not APPROVED"
        ),
    }


# Pre-registered thresholds for LEDA-6 (locked; report all; do not pick on test)
LEDA6_VOL_VETO_THRESHOLDS: tuple[float, ...] = (0.70, 0.80, 0.90, 0.95)


def evaluate_vol_veto_threshold_grid(
    ohlcv: pd.DataFrame,
    *,
    thresholds: tuple[float, ...] | list[float] = LEDA6_VOL_VETO_THRESHOLDS,
    costs: CostConfig | None = None,
    splits: SplitConfig | None = None,
    gates: GateConfig | None = None,
    timeframe: str = "1d",
    config_path: str | None = None,
) -> dict[str, Any]:
    """LEDA-6: pre-registered multi-threshold vol-veto study.

    Evaluates **every** threshold on train/val/test. Does not select a winner
    for promotion. Multiplicity: n_thresholds trials in the family.
    """
    cfg = load_config(config_path)
    costs = costs or cost_from_config(cfg)
    splits = splits or splits_from_config(cfg)
    gates = gates or gates_from_config(cfg)

    thr_list = [float(t) for t in thresholds]
    for t in thr_list:
        if not (0.0 < t <= 1.0):
            raise ValueError(f"invalid threshold {t}")

    results: list[dict[str, Any]] = []
    for t in thr_list:
        one = evaluate_vol_veto_policy(
            ohlcv,
            costs=costs,
            splits=splits,
            gates=gates,
            risk_veto_threshold=t,
            timeframe=timeframe,
            config_path=config_path,
        )
        results.append(
            {
                "threshold": t,
                "full_sample_long_frac": one["full_sample_long_frac"],
                "slices": one["slices"],
                "gate_checklist_test": one["gate_checklist_test"],
                "exploratory_hard_gates_pass": one["exploratory_hard_gates_pass"],
            }
        )

    # Honest summary: count how many pass diagnostic hard gates (not promotion)
    n_pass = sum(1 for r in results if r["exploratory_hard_gates_pass"])
    # Prefer describing test excess vs B&H without crowning a champion
    test_excess = {
        str(r["threshold"]): r["slices"]["test"]["excess_return_vs_bh"] for r in results
    }

    return {
        "leda": "6",
        "mode": "exploratory",
        "promotion": "not_approved — multi-threshold diagnostic; no winner selection",
        "family": "leda6_vol_veto_thresholds",
        "n_thresholds": len(thr_list),
        "thresholds_preregistered": thr_list,
        "channel_ids": ["leda1_vol_risk"],
        "results_by_threshold": results,
        "n_pass_exploratory_hard_gates": n_pass,
        "test_excess_return_vs_bh_by_threshold": test_excess,
        "note": (
            f"Family size = {len(thr_list)}. Report all cells. "
            "Do not pick the best test threshold for promotion or shadow."
        ),
    }
