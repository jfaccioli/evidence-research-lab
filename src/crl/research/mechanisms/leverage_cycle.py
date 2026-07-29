"""Mechanism study: leverage build and unwind sequences.

Mechanism id: leverage_cycle
Question: How does leverage build and unwind?

Hypothesis (locked for study v1):
  Leverage *build* (rising OI and elevated |funding| or premium) precedes
  elevated next-RV more often than leverage *unwind* (falling OI). Build and
  unwind are sequential states, not a multi-factor trade score.

Design (pre-registered, causal, NOT trading):
  - OI change: oi_chg_pct_1d lagged (PIT as-of)
  - Build state: oi_chg_pct_lag > expanding p75 AND (abs_funding or abs_premium) > p50
  - Unwind state: oi_chg_pct_lag < expanding p25
  - Quiet leverage: neither build nor unwind
  - Outcomes: mean/median rv_next; P(high rv_next); mean fwd_ret (descriptive)
  - No position rules. No LEDA open by default.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.research.market_properties.synthesis import build_property_panel
from crl.shared.data.oi import add_oi_features

MECHANISM_ID = "leverage_cycle"
STUDY_VERSION = 1


def _expanding_q(s: pd.Series, q: float, min_periods: int = 60) -> pd.Series:
    vals = s.to_numpy(dtype=float)
    out = np.full(len(vals), np.nan)
    for i in range(len(vals)):
        if i + 1 < min_periods or not np.isfinite(vals[i]):
            continue
        w = vals[: i + 1]
        w = w[np.isfinite(w)]
        if len(w) < min_periods:
            continue
        out[i] = float(np.quantile(w, q))
    return pd.Series(out, index=s.index)


def _slice_stats(
    mask: np.ndarray, rv_next: np.ndarray, fwd: np.ndarray, high_rv: np.ndarray
) -> dict[str, Any]:
    m = mask & np.isfinite(rv_next)
    n = int(m.sum())
    if n < 30:
        return {"n": n, "ok": False, "reason": "n<30"}
    return {
        "n": n,
        "ok": True,
        "mean_rv_next": round(float(np.mean(rv_next[m])), 8),
        "median_rv_next": round(float(np.median(rv_next[m])), 8),
        "p_high_rv_next": round(float(np.mean(high_rv[m])), 6),
        "mean_fwd_ret": round(float(np.mean(fwd[m])), 8),
    }


def study_leverage_cycle(
    ohlcv: pd.DataFrame,
    *,
    oi_events: Optional[pd.DataFrame] = None,
    premium_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    min_periods: int = 60,
) -> dict[str, Any]:
    if oi_events is None or len(oi_events) == 0:
        return {
            "ok": False,
            "mechanism_id": MECHANISM_ID,
            "reason": "oi_events required for leverage_cycle v1",
        }

    feat = add_oi_features(ohlcv, oi_events)
    panel = build_property_panel(
        ohlcv,
        premium_events=premium_events,
        funding_events=funding_events,
    )
    # Align OI features
    panel["oi_chg_pct_lag"] = feat["oi_chg_pct_1d"].shift(1)
    panel["oi_last_lag"] = feat["oi_last"].shift(1)

    thr_oi_hi = _expanding_q(panel["oi_chg_pct_lag"], 0.75, min_periods)
    thr_oi_lo = _expanding_q(panel["oi_chg_pct_lag"], 0.25, min_periods)

    lev_proxy = None
    if "abs_funding_lag" in panel.columns:
        lev_proxy = panel["abs_funding_lag"]
    elif "abs_premium_lag" in panel.columns:
        lev_proxy = panel["abs_premium_lag"]
    thr_lev = (
        _expanding_q(lev_proxy, 0.5, min_periods) if lev_proxy is not None else None
    )

    build = (panel["oi_chg_pct_lag"] > thr_oi_hi) & thr_oi_hi.notna()
    if thr_lev is not None and lev_proxy is not None:
        build = build & (lev_proxy >= thr_lev) & thr_lev.notna()
    unwind = (panel["oi_chg_pct_lag"] < thr_oi_lo) & thr_oi_lo.notna()
    quiet = (~build) & (~unwind) & panel["oi_chg_pct_lag"].notna()

    base = panel.dropna(subset=["rv_lag", "rv_next", "oi_chg_pct_lag"]).copy()
    thr_rv = _expanding_q(base["rv_lag"], 0.5, min_periods)
    high_next = (base["rv_next"] >= thr_rv.reindex(base.index)).fillna(False)

    rv_n = base["rv_next"].to_numpy(dtype=float)
    fwd = base["fwd_ret"].to_numpy(dtype=float) if "fwd_ret" in base.columns else np.zeros(len(base))
    hn = high_next.to_numpy()

    states = {
        "build": _slice_stats(build.reindex(base.index).fillna(False).to_numpy(), rv_n, fwd, hn),
        "unwind": _slice_stats(unwind.reindex(base.index).fillna(False).to_numpy(), rv_n, fwd, hn),
        "quiet": _slice_stats(quiet.reindex(base.index).fillna(False).to_numpy(), rv_n, fwd, hn),
        "unconditional": _slice_stats(np.ones(len(base), dtype=bool), rv_n, fwd, hn),
    }

    # Hypothesis check: build mean_rv_next > unwind mean_rv_next by margin
    b_ok = states["build"].get("ok") and states["unwind"].get("ok")
    margin = None
    supports = False
    if b_ok:
        margin = round(
            states["build"]["mean_rv_next"] - states["unwind"]["mean_rv_next"], 8
        )
        supports = margin >= 0.001  # material absolute margin on daily RV std scale

    return {
        "ok": True,
        "mechanism_id": MECHANISM_ID,
        "study_version": STUDY_VERSION,
        "hypothesis": (
            "Leverage build (rising OI + elevated funding/premium stress) precedes "
            "higher next-RV than leverage unwind (falling OI)"
        ),
        "design": {
            "build": "oi_chg_pct_lag > expanding p75 AND abs leverage proxy >= expanding p50",
            "unwind": "oi_chg_pct_lag < expanding p25",
            "leverage_proxy": "abs_funding_lag if present else abs_premium_lag",
            "min_periods": min_periods,
        },
        "n_bars": len(base),
        "states": states,
        "build_minus_unwind_mean_rv_next": margin,
        "interpretation": {
            "hypothesis_supported_under_margin": supports,
            "note": (
                "Descriptive sequence study only. Not a trade map. "
                "Null or weak margin → do not invent leverage-timing signals."
            ),
        },
        "leda_candidate": False,
        "promotion": "not_applicable — mechanism study only",
        "preregistered_candidate": False,
    }
