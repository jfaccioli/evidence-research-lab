"""Market property: aggregate stablecoin circulating supply (liquidity stock).

Distinct from:
- exchange stablecoin *netflow* (already conf-null as atomistic filters)
- spot OHLCV transforms
- funding / premium (futures leverage)

Measures total pegged-USD circulating supply (DefiLlama). Growth rates describe
crypto-wide liquidity expansion/contraction.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.shared.data.stablecoin_supply import validate_supply_events

PROPERTY_ID = "stablecoin_agg_supply"
PROPERTY_VERSION = 1


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 20:
        return None
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return None
    v = float(np.corrcoef(a, b)[0, 1])
    return None if v != v else round(v, 6)


def align_supply_to_ohlcv(
    ohlcv: pd.DataFrame,
    supply_events: pd.DataFrame,
) -> pd.DataFrame:
    """PIT as-of: last supply event_time ≤ bar timestamp."""
    ev = validate_supply_events(supply_events)
    bars = (
        ohlcv.index.tz_convert("UTC")
        if ohlcv.index.tz is not None
        else ohlcv.index.tz_localize("UTC")
    )
    # Harmonize datetime unit for merge_asof (ms vs us mismatch fails)
    bars = pd.DatetimeIndex(pd.to_datetime(bars, utc=True)).as_unit("ns")
    left = pd.DataFrame({"bar_ts": bars}).sort_values("bar_ts")
    right = ev.rename(columns={"event_time": "sup_time", "supply_usd": "supply"})
    right["sup_time"] = pd.DatetimeIndex(
        pd.to_datetime(right["sup_time"], utc=True)
    ).as_unit("ns")
    right = right.sort_values("sup_time")
    merged = pd.merge_asof(
        left, right, left_on="bar_ts", right_on="sup_time", direction="backward"
    )
    supply = pd.Series(merged["supply"].to_numpy(), index=ohlcv.index, dtype=float)
    # log growth over 7d and 30d (level is nonstationary)
    dlog_7 = np.log(supply / supply.shift(7))
    dlog_30 = np.log(supply / supply.shift(30))
    close = ohlcv["close"].astype(float)
    log_ret = np.log(close / close.shift(1))
    rv_end = log_ret.rolling(20, min_periods=20).std()

    return pd.DataFrame(
        {
            "supply_usd": supply.to_numpy(),
            "supply_dlog_7": dlog_7.to_numpy(),
            "supply_dlog_30": dlog_30.to_numpy(),
            "supply_dlog_7_lag": dlog_7.shift(1).to_numpy(),
            "supply_dlog_30_lag": dlog_30.shift(1).to_numpy(),
            "log_ret": log_ret.to_numpy(),
            "ret_lag": log_ret.shift(1).to_numpy(),
            "rv_lag": rv_end.shift(1).to_numpy(),
            "rv_next": rv_end.shift(-1).to_numpy(),
            "fwd_ret": log_ret.shift(-1).to_numpy(),
            "property_id": PROPERTY_ID,
            "version": PROPERTY_VERSION,
        },
        index=ohlcv.index,
    )


def characterize_stablecoin_supply(
    ohlcv: pd.DataFrame,
    supply_events: pd.DataFrame,
    *,
    funding_events: Optional[pd.DataFrame] = None,
    premium_events: Optional[pd.DataFrame] = None,
    min_points: int = 100,
) -> dict[str, Any]:
    """Characterize aggregate stable supply growth — not a trade map."""
    frame = align_supply_to_ohlcv(ohlcv, supply_events)

    if funding_events is not None and len(funding_events):
        from crl.research.market_properties.perp_premium import _align_funding_daily

        frame["funding_lag"] = _align_funding_daily(ohlcv, funding_events).shift(1)
    if premium_events is not None and len(premium_events):
        from crl.research.market_properties.perp_premium import align_premium_to_ohlcv

        prem = align_premium_to_ohlcv(ohlcv, premium_events)
        frame["premium_lag"] = prem["premium_lag"]

    need = [
        "supply_dlog_7_lag",
        "supply_dlog_30_lag",
        "ret_lag",
        "rv_lag",
        "rv_next",
        "fwd_ret",
    ]
    df = frame.dropna(subset=need)
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "property_id": PROPERTY_ID,
            "n": n,
            "reason": f"need >= {min_points} aligned bars",
        }

    g7 = df["supply_dlog_7_lag"].to_numpy(dtype=float)
    g30 = df["supply_dlog_30_lag"].to_numpy(dtype=float)
    ret_l = df["ret_lag"].to_numpy(dtype=float)
    rv_l = df["rv_lag"].to_numpy(dtype=float)
    rv_n = df["rv_next"].to_numpy(dtype=float)
    fwd = df["fwd_ret"].to_numpy(dtype=float)

    independence: dict[str, Any] = {
        "corr_dlog7_vs_ret_lag": _safe_corr(g7, ret_l),
        "corr_dlog7_vs_rv_lag": _safe_corr(g7, rv_l),
        "corr_dlog30_vs_ret_lag": _safe_corr(g30, ret_l),
        "corr_dlog30_vs_rv_lag": _safe_corr(g30, rv_l),
        "corr_dlog7_vs_dlog30": _safe_corr(g7, g30),
    }
    if "funding_lag" in df.columns:
        fl = df["funding_lag"].to_numpy(dtype=float)
        m = np.isfinite(fl)
        independence["corr_dlog7_vs_funding_lag"] = _safe_corr(g7[m], fl[m])
    if "premium_lag" in df.columns:
        pl = df["premium_lag"].to_numpy(dtype=float)
        m = np.isfinite(pl)
        independence["corr_dlog7_vs_premium_lag"] = _safe_corr(g7[m], pl[m])

    skill = {
        "corr_dlog7_vs_fwd_ret": _safe_corr(g7, fwd),
        "corr_dlog7_vs_rv_next": _safe_corr(g7, rv_n),
        "corr_dlog30_vs_fwd_ret": _safe_corr(g30, fwd),
        "corr_dlog30_vs_rv_next": _safe_corr(g30, rv_n),
    }

    # High growth vs contraction
    hi = g7 >= np.nanpercentile(g7, 80)
    lo = g7 <= np.nanpercentile(g7, 20)
    cond = {
        "mean_fwd_ret_dlog7_ge_p80": (
            round(float(np.mean(fwd[hi])), 8) if hi.any() else None
        ),
        "mean_fwd_ret_dlog7_le_p20": (
            round(float(np.mean(fwd[lo])), 8) if lo.any() else None
        ),
        "mean_rv_next_dlog7_ge_p80": (
            round(float(np.mean(rv_n[hi])), 8) if hi.any() else None
        ),
        "mean_rv_next_dlog7_le_p20": (
            round(float(np.mean(rv_n[lo])), 8) if lo.any() else None
        ),
    }

    abs_dir = abs(skill["corr_dlog7_vs_fwd_ret"] or 0.0)
    abs_unc = abs(skill["corr_dlog7_vs_rv_next"] or 0.0)
    abs_ret_ind = abs(independence["corr_dlog7_vs_ret_lag"] or 0.0)

    if abs_unc > abs_dir + 0.02:
        role = "uncertainty / liquidity stress more than direction"
    elif abs_dir > abs_unc + 0.02:
        role = "direction / risk-on liquidity more than uncertainty"
    else:
        role = "weak linear association with both direction and next RV"

    supply_level = frame["supply_usd"].dropna()
    coverage = {
        "n_bars_ohlcv": len(ohlcv),
        "n_supply_events": len(supply_events),
        "n_aligned": n,
        "supply_usd_start": round(float(supply_level.iloc[0]), 2) if len(supply_level) else None,
        "supply_usd_end": round(float(supply_level.iloc[-1]), 2) if len(supply_level) else None,
        "dlog7_mean": round(float(np.mean(g7)), 8),
        "dlog7_std": round(float(np.std(g7, ddof=1)), 8),
    }

    return {
        "ok": True,
        "property_id": PROPERTY_ID,
        "version": PROPERTY_VERSION,
        "what_it_measures": (
            "Aggregate stablecoin circulating supply (USD pegged) and its "
            "7d/30d log growth — crypto liquidity stock, not exchange flow"
        ),
        "putative_mechanism": (
            "Stablecoin mint/burn and capital entry/exit into crypto; "
            "liquidity stock may condition risk appetite and volatility"
        ),
        "primary_role_guess": role,
        "coverage": coverage,
        "independence_vs_known_properties": independence,
        "association_next_state": skill,
        "conditional": cond,
        "interpretation": {
            "more_about_uncertainty_than_direction": bool(abs_unc > abs_dir + 0.02),
            "partially_independent_of_ret_lag": bool(abs_ret_ind < 0.5),
            "distinct_from_futures_leverage_state": bool(
                abs(independence.get("corr_dlog7_vs_funding_lag") or 0.0) < 0.4
                and abs(independence.get("corr_dlog7_vs_premium_lag") or 0.0) < 0.4
            ),
            "note": (
                "Characterization only. Not exchange netflow. No LEDA promotion. "
                "Understanding of liquidity stock is valuable even without edge."
            ),
        },
        "improves_understanding_without_edge": True,
        "promotion": "not_applicable — market property characterization only",
        "leda_candidate": False,
        "leda_note": (
            "Consider risk/state channel only if independence holds and a "
            "pre-registered claim on uncertainty or regime is locked"
        ),
        "next_science": (
            "If growth co-moves with future RV or risk-on returns materially, "
            "pre-reg state channel; else document null and retire linear claim"
        ),
    }
