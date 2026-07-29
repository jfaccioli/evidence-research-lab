"""Market property: kline aggression / trade intensity.

Measures (from Binance-style klines; not close transforms):

- ``taker_buy_ratio`` = taker_buy_base / volume  (aggressive buyer share)
- ``trade_intensity`` = n_trades                 (activity count)
- ``avg_trade_size`` = volume / n_trades         (ticket size proxy)

Scientific questions (characterization, not trade rules):

1. What does this measure? Under what mechanism?
2. How independent is it from properties already known?
3. Direction, uncertainty, liquidity, participation, or structure?
4. Does it improve understanding even without a trading edge?

No portfolio mapping here. LEDA channel only after characterization + pre-reg.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

PROPERTY_ID = "kline_aggression"
PROPERTY_VERSION = 1
# Back-compat aliases
OBSERVATION_FAMILY_ID = PROPERTY_ID
OBSERVATION_VERSION = PROPERTY_VERSION


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
            f"{PROPERTY_ID}: missing columns {sorted(missing)}; "
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
            "property_id": PROPERTY_ID,
            "family_id": PROPERTY_ID,
            "version": PROPERTY_VERSION,
        },
        index=ohlcv.index,
    )


def characterize_kline_aggression(
    ohlcv: pd.DataFrame,
    *,
    min_points: int = 100,
) -> dict[str, Any]:
    """Characterize the market property — not a trading promotion gate."""
    try:
        frame = build_aggression_frame(ohlcv)
    except ValueError as e:
        return {
            "ok": False,
            "property_id": PROPERTY_ID,
            "family_id": PROPERTY_ID,
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
            "property_id": PROPERTY_ID,
            "family_id": PROPERTY_ID,
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
        "property_id": PROPERTY_ID,
        "family_id": PROPERTY_ID,
        "version": PROPERTY_VERSION,
        "what_it_measures": (
            "Aggressive buyer share of volume and number of trades per bar "
            "(spot kline microstructure)"
        ),
        "putative_mechanism": (
            "Taker aggression reflects marketable-order imbalance; trade count "
            "reflects participation/activity intensity"
        ),
        "primary_role_guess": "participation / activity; weak direction for tbr",
        "claim": (
            "Taker buy share and trade intensity are bar-level microstructure "
            "properties independent of pure close transforms"
        ),
        "coverage": coverage,
        "independence_vs_known_properties": ind,
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
        "improves_understanding_without_edge": True,
        "promotion": "not_applicable — market property characterization only",
        "leda_candidate": False,
        "leda_note": "Only after pre-reg state/risk claim; not automatic",
        "next_science": (
            "Trade intensity shows clearer next-RV association than direction; "
            "taker_buy_ratio co-moves with same-bar returns."
        ),
    }
