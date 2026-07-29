"""Observation family: kline aggression / trade intensity.

Measurable properties (from Binance-style klines; not close transforms):

- ``taker_buy_ratio`` = taker_buy_base / volume  (aggressive buyer share)
- ``trade_intensity`` = n_trades                 (activity count)
- ``avg_trade_size`` = volume / n_trades         (ticket size proxy)

Scientific questions (characterization, not trade rules):

1. Are these finite, stable observables on real bars?
2. How independent are they from lagged returns and lagged RV?
3. Do they associate with *next* RV (uncertainty) more than *next* return (direction)?

No portfolio mapping here. LEDA channel only after pre-reg programme.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

OBSERVATION_FAMILY_ID = "kline_aggression"
OBSERVATION_VERSION = 1


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 20:
        return None
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return None
    v = float(np.corrcoef(a, b)[0, 1])
    return None if v != v else round(v, 6)


def build_aggression_frame(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Build PIT observation series; requires microstructure columns."""
    need = {"close", "volume", "taker_buy_base", "n_trades"}
    missing = need - set(ohlcv.columns)
    if missing:
        raise ValueError(
            f"{OBSERVATION_FAMILY_ID}: missing columns {sorted(missing)}; "
            "re-fetch with binance_public (kline micro fields) or use mock"
        )

    vol = ohlcv["volume"].astype(float)
    tb = ohlcv["taker_buy_base"].astype(float)
    nt = ohlcv["n_trades"].astype(float)
    close = ohlcv["close"].astype(float)

    # Clip ratio into [0,1]; zero volume → NaN (fail closed for that bar)
    with np.errstate(divide="ignore", invalid="ignore"):
        tbr = tb / vol.replace(0.0, np.nan)
    tbr = tbr.clip(0.0, 1.0)
    intensity = nt.replace(0.0, np.nan)
    avg_sz = vol / intensity

    log_ret = np.log(close / close.shift(1))
    # Lagged observations (decision-time at t uses bar t-1 close micro)
    tbr_lag = tbr.shift(1)
    intensity_lag = intensity.shift(1)
    # Contemporaneous for description only
    rv_end = log_ret.rolling(20, min_periods=20).std()
    rv_lag = rv_end.shift(1)
    rv_next = rv_end.shift(-1)
    ret_lag = log_ret.shift(1)
    fwd_ret = log_ret.shift(-1)

    return pd.DataFrame(
        {
            "taker_buy_ratio": tbr.to_numpy(),
            "taker_buy_ratio_lag": tbr_lag.to_numpy(),
            "trade_intensity": intensity.to_numpy(),
            "trade_intensity_lag": intensity_lag.to_numpy(),
            "avg_trade_size": avg_sz.to_numpy(),
            "log_ret": log_ret.to_numpy(),
            "ret_lag": ret_lag.to_numpy(),
            "rv_lag": rv_lag.to_numpy(),
            "rv_next": rv_next.to_numpy(),
            "fwd_ret": fwd_ret.to_numpy(),
            "family_id": OBSERVATION_FAMILY_ID,
            "version": OBSERVATION_VERSION,
        },
        index=ohlcv.index,
    )


def characterize_kline_aggression(
    ohlcv: pd.DataFrame,
    *,
    min_points: int = 100,
) -> dict[str, Any]:
    """Characterize the observation — not a trading promotion gate."""
    try:
        frame = build_aggression_frame(ohlcv)
    except ValueError as e:
        return {
            "ok": False,
            "family_id": OBSERVATION_FAMILY_ID,
            "reason": str(e),
        }

    df = frame.dropna(
        subset=[
            "taker_buy_ratio_lag",
            "trade_intensity_lag",
            "ret_lag",
            "rv_lag",
            "rv_next",
            "fwd_ret",
        ]
    )
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "family_id": OBSERVATION_FAMILY_ID,
            "n": n,
            "reason": f"need >= {min_points} finite bars with micro columns",
        }

    tbr = df["taker_buy_ratio_lag"].to_numpy(dtype=float)
    inten = np.log(df["trade_intensity_lag"].to_numpy(dtype=float))  # scale
    ret_l = df["ret_lag"].to_numpy(dtype=float)
    rv_l = df["rv_lag"].to_numpy(dtype=float)
    rv_n = df["rv_next"].to_numpy(dtype=float)
    fwd = df["fwd_ret"].to_numpy(dtype=float)

    # Independence-ish: |corr| with already-used series
    ind = {
        "corr_tbr_vs_ret_lag": _safe_corr(tbr, ret_l),
        "corr_tbr_vs_rv_lag": _safe_corr(tbr, rv_l),
        "corr_log_intensity_vs_ret_lag": _safe_corr(inten, ret_l),
        "corr_log_intensity_vs_rv_lag": _safe_corr(inten, rv_l),
        "corr_tbr_vs_log_intensity": _safe_corr(tbr, inten),
    }
    # Uncertainty vs direction
    skill = {
        "corr_tbr_vs_rv_next": _safe_corr(tbr, rv_n),
        "corr_tbr_vs_fwd_ret": _safe_corr(tbr, fwd),
        "corr_log_intensity_vs_rv_next": _safe_corr(inten, rv_n),
        "corr_log_intensity_vs_fwd_ret": _safe_corr(inten, fwd),
    }

    # Descriptive coverage
    tbr_raw = frame["taker_buy_ratio"].dropna()
    coverage = {
        "n_bars": len(ohlcv),
        "n_characterized": n,
        "taker_buy_ratio_mean": round(float(tbr_raw.mean()), 6),
        "taker_buy_ratio_std": round(float(tbr_raw.std(ddof=1)), 6),
        "frac_tbr_outside_0_4_0_6": round(
            float(((tbr_raw < 0.4) | (tbr_raw > 0.6)).mean()), 6
        ),
    }

    # Heuristic flags for research director (not gates)
    abs_tbr_dir = abs(skill["corr_tbr_vs_fwd_ret"] or 0.0)
    abs_tbr_unc = abs(skill["corr_tbr_vs_rv_next"] or 0.0)
    abs_int_dir = abs(skill["corr_log_intensity_vs_fwd_ret"] or 0.0)
    abs_int_unc = abs(skill["corr_log_intensity_vs_rv_next"] or 0.0)
    abs_ind_ret = abs(ind["corr_tbr_vs_ret_lag"] or 0.0)

    return {
        "ok": True,
        "family_id": OBSERVATION_FAMILY_ID,
        "version": OBSERVATION_VERSION,
        "claim": (
            "Taker buy share and trade intensity are bar-level microstructure "
            "observations independent of pure close transforms"
        ),
        "coverage": coverage,
        "independence_vs_used_series": ind,
        "association_next_state": skill,
        "interpretation": {
            "tbr_more_about_uncertainty_than_direction": bool(
                abs_tbr_unc > abs_tbr_dir + 0.02
            ),
            "intensity_more_about_uncertainty_than_direction": bool(
                abs_int_unc > abs_int_dir + 0.02
            ),
            "tbr_partially_independent_of_ret_lag": bool(abs_ind_ret < 0.5),
            "note": (
                "Flags are descriptive. Do not promote to LEDA trade map "
                "without pre-registered programme and frozen gates."
            ),
        },
        "promotion": "not_applicable — observation characterization only",
        "next_science": (
            "Trade intensity shows clearer next-RV association than direction; "
            "taker_buy_ratio co-moves with same-bar returns. "
            "Pre-register a *state/risk* evidence channel if pursuing — not mom long."
        ),
    }
