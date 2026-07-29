"""Market property: cross-venue spot basis (Binance USDT vs Coinbase USD).

Measures relative dislocation between two major spot venues (log price ratio).
Includes USD/USDT wedge as part of the measured object (not pure FX-free).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.shared.data.cross_venue import validate_basis_events

PROPERTY_ID = "cross_venue_basis"
PROPERTY_VERSION = 1


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 20:
        return None
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return None
    v = float(np.corrcoef(a, b)[0, 1])
    return None if v != v else round(v, 6)


def align_basis_to_ohlcv(
    ohlcv: pd.DataFrame, basis_events: pd.DataFrame
) -> pd.DataFrame:
    ev = validate_basis_events(basis_events)
    bars = (
        ohlcv.index.tz_convert("UTC")
        if ohlcv.index.tz is not None
        else ohlcv.index.tz_localize("UTC")
    )
    bars = pd.DatetimeIndex(pd.to_datetime(bars, utc=True)).as_unit("ns")
    left = pd.DataFrame({"bar_ts": bars}).sort_values("bar_ts")
    right = ev.rename(columns={"event_time": "b_time", "basis": "basis"})
    right["b_time"] = pd.DatetimeIndex(pd.to_datetime(right["b_time"], utc=True)).as_unit(
        "ns"
    )
    right = right.sort_values("b_time")
    merged = pd.merge_asof(
        left, right, left_on="bar_ts", right_on="b_time", direction="backward"
    )
    basis = pd.Series(merged["basis"].to_numpy(), index=ohlcv.index, dtype=float)
    close = ohlcv["close"].astype(float)
    log_ret = np.log(close / close.shift(1))
    rv_end = log_ret.rolling(20, min_periods=20).std()
    return pd.DataFrame(
        {
            "basis": basis.to_numpy(),
            "basis_lag": basis.shift(1).to_numpy(),
            "abs_basis_lag": basis.shift(1).abs().to_numpy(),
            "ret_lag": log_ret.shift(1).to_numpy(),
            "rv_lag": rv_end.shift(1).to_numpy(),
            "rv_next": rv_end.shift(-1).to_numpy(),
            "fwd_ret": log_ret.shift(-1).to_numpy(),
            "property_id": PROPERTY_ID,
            "version": PROPERTY_VERSION,
        },
        index=ohlcv.index,
    )


def characterize_cross_venue_basis(
    ohlcv: pd.DataFrame,
    basis_events: pd.DataFrame,
    *,
    min_points: int = 100,
) -> dict[str, Any]:
    frame = align_basis_to_ohlcv(ohlcv, basis_events)
    df = frame.dropna(subset=["basis_lag", "ret_lag", "rv_lag", "rv_next", "fwd_ret"])
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "property_id": PROPERTY_ID,
            "n": n,
            "reason": f"need >= {min_points}",
        }
    b = df["basis_lag"].to_numpy(dtype=float)
    ab = df["abs_basis_lag"].to_numpy(dtype=float)
    ret_l = df["ret_lag"].to_numpy(dtype=float)
    rv_l = df["rv_lag"].to_numpy(dtype=float)
    rv_n = df["rv_next"].to_numpy(dtype=float)
    fwd = df["fwd_ret"].to_numpy(dtype=float)

    skill = {
        "corr_basis_lag_vs_fwd_ret": _safe_corr(b, fwd),
        "corr_abs_basis_lag_vs_fwd_ret": _safe_corr(ab, fwd),
        "corr_abs_basis_lag_vs_rv_next": _safe_corr(ab, rv_n),
        "autocorr_basis": _safe_corr(b[:-1], b[1:]) if len(b) > 30 else None,
    }
    independence = {
        "corr_basis_vs_ret_lag": _safe_corr(b, ret_l),
        "corr_abs_basis_vs_rv_lag": _safe_corr(ab, rv_l),
    }
    abs_dir = abs(skill["corr_abs_basis_lag_vs_fwd_ret"] or 0.0)
    abs_unc = abs(skill["corr_abs_basis_lag_vs_rv_next"] or 0.0)
    return {
        "ok": True,
        "property_id": PROPERTY_ID,
        "version": PROPERTY_VERSION,
        "what_it_measures": (
            "log(Binance BTCUSDT close / Coinbase BTC-USD close) — multi-venue "
            "spot dislocation including USD/USDT wedge"
        ),
        "putative_mechanism": (
            "Venue inventory, payment rail, and USD/USDT funding differences; "
            "elevated |basis| may mark fragmentation/stress"
        ),
        "primary_role_guess": (
            "market dislocation / fragmentation"
            if abs_unc >= abs_dir
            else "direction or dislocation"
        ),
        "coverage": {
            "n_aligned": n,
            "basis_mean": round(float(np.mean(b)), 8),
            "basis_std": round(float(np.std(b, ddof=1)), 8),
            "abs_basis_mean": round(float(np.mean(ab)), 8),
        },
        "independence_vs_known_properties": independence,
        "association_next_state": skill,
        "interpretation": {
            "more_about_uncertainty_than_direction": bool(abs_unc > abs_dir + 0.02),
            "note": "Characterization only. No LEDA promotion.",
        },
        "improves_understanding_without_edge": True,
        "promotion": "not_applicable — market property characterization only",
        "leda_candidate": False,
    }
