"""Market property: aggregate DeFi TVL (capital locked in DeFi).

Distinct from stablecoin circulating supply (liquidity stock in pegged assets)
and from futures leverage state. Measures capital committed to DeFi protocols.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.shared.data.defi_tvl import validate_tvl_events

PROPERTY_ID = "defi_agg_tvl"
PROPERTY_VERSION = 1


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 20:
        return None
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return None
    v = float(np.corrcoef(a, b)[0, 1])
    return None if v != v else round(v, 6)


def align_tvl_to_ohlcv(ohlcv: pd.DataFrame, tvl_events: pd.DataFrame) -> pd.DataFrame:
    ev = validate_tvl_events(tvl_events)
    bars = (
        ohlcv.index.tz_convert("UTC")
        if ohlcv.index.tz is not None
        else ohlcv.index.tz_localize("UTC")
    )
    bars = pd.DatetimeIndex(pd.to_datetime(bars, utc=True)).as_unit("ns")
    left = pd.DataFrame({"bar_ts": bars}).sort_values("bar_ts")
    right = ev.rename(columns={"event_time": "tvl_time", "tvl_usd": "tvl"})
    right["tvl_time"] = pd.DatetimeIndex(
        pd.to_datetime(right["tvl_time"], utc=True)
    ).as_unit("ns")
    right = right.sort_values("tvl_time")
    merged = pd.merge_asof(
        left, right, left_on="bar_ts", right_on="tvl_time", direction="backward"
    )
    tvl = pd.Series(merged["tvl"].to_numpy(), index=ohlcv.index, dtype=float)
    dlog_7 = np.log(tvl / tvl.shift(7))
    dlog_30 = np.log(tvl / tvl.shift(30))
    close = ohlcv["close"].astype(float)
    log_ret = np.log(close / close.shift(1))
    rv_end = log_ret.rolling(20, min_periods=20).std()
    return pd.DataFrame(
        {
            "tvl_usd": tvl.to_numpy(),
            "tvl_dlog_7_lag": dlog_7.shift(1).to_numpy(),
            "tvl_dlog_30_lag": dlog_30.shift(1).to_numpy(),
            "ret_lag": log_ret.shift(1).to_numpy(),
            "rv_lag": rv_end.shift(1).to_numpy(),
            "rv_next": rv_end.shift(-1).to_numpy(),
            "fwd_ret": log_ret.shift(-1).to_numpy(),
            "property_id": PROPERTY_ID,
            "version": PROPERTY_VERSION,
        },
        index=ohlcv.index,
    )


def characterize_defi_tvl(
    ohlcv: pd.DataFrame,
    tvl_events: pd.DataFrame,
    *,
    supply_events: Optional[pd.DataFrame] = None,
    funding_events: Optional[pd.DataFrame] = None,
    premium_events: Optional[pd.DataFrame] = None,
    min_points: int = 100,
) -> dict[str, Any]:
    frame = align_tvl_to_ohlcv(ohlcv, tvl_events)
    if supply_events is not None and len(supply_events):
        from crl.research.market_properties.stablecoin_supply import align_supply_to_ohlcv

        s = align_supply_to_ohlcv(ohlcv, supply_events)
        frame["supply_dlog7_lag"] = s["supply_dlog_7_lag"]
    if funding_events is not None and len(funding_events):
        from crl.research.market_properties.perp_premium import _align_funding_daily

        frame["funding_lag"] = _align_funding_daily(ohlcv, funding_events).shift(1)
    if premium_events is not None and len(premium_events):
        from crl.research.market_properties.perp_premium import align_premium_to_ohlcv

        frame["premium_lag"] = align_premium_to_ohlcv(ohlcv, premium_events)[
            "premium_lag"
        ]

    need = ["tvl_dlog_7_lag", "tvl_dlog_30_lag", "ret_lag", "rv_lag", "rv_next", "fwd_ret"]
    df = frame.dropna(subset=need)
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "property_id": PROPERTY_ID,
            "n": n,
            "reason": f"need >= {min_points}",
        }

    g7 = df["tvl_dlog_7_lag"].to_numpy(dtype=float)
    g30 = df["tvl_dlog_30_lag"].to_numpy(dtype=float)
    ret_l = df["ret_lag"].to_numpy(dtype=float)
    rv_l = df["rv_lag"].to_numpy(dtype=float)
    rv_n = df["rv_next"].to_numpy(dtype=float)
    fwd = df["fwd_ret"].to_numpy(dtype=float)

    independence: dict[str, Any] = {
        "corr_dlog7_vs_ret_lag": _safe_corr(g7, ret_l),
        "corr_dlog7_vs_rv_lag": _safe_corr(g7, rv_l),
        "corr_dlog30_vs_rv_lag": _safe_corr(g30, rv_l),
    }
    if "supply_dlog7_lag" in df.columns:
        s7 = df["supply_dlog7_lag"].to_numpy(dtype=float)
        m = np.isfinite(s7)
        independence["corr_tvl_dlog7_vs_stable_dlog7"] = _safe_corr(g7[m], s7[m])
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
    abs_dir = abs(skill["corr_dlog7_vs_fwd_ret"] or 0.0)
    abs_unc = abs(skill["corr_dlog7_vs_rv_next"] or 0.0)
    role = (
        "uncertainty / risk-on capital more than direction"
        if abs_unc > abs_dir + 0.02
        else (
            "direction more than uncertainty"
            if abs_dir > abs_unc + 0.02
            else "weak linear association with both"
        )
    )
    tvl_level = frame["tvl_usd"].dropna()
    return {
        "ok": True,
        "property_id": PROPERTY_ID,
        "version": PROPERTY_VERSION,
        "what_it_measures": (
            "Aggregate DeFi TVL (USD locked in protocols) and 7d/30d log growth"
        ),
        "putative_mechanism": (
            "Capital allocation into DeFi smart contracts — risk-on crypto "
            "commitment distinct from circulating stable stock"
        ),
        "primary_role_guess": role,
        "coverage": {
            "n_aligned": n,
            "n_tvl_events": len(tvl_events),
            "tvl_usd_end": round(float(tvl_level.iloc[-1]), 2) if len(tvl_level) else None,
            "dlog7_mean": round(float(np.mean(g7)), 8),
            "dlog7_std": round(float(np.std(g7, ddof=1)), 8),
        },
        "independence_vs_known_properties": independence,
        "association_next_state": skill,
        "interpretation": {
            "more_about_uncertainty_than_direction": bool(abs_unc > abs_dir + 0.02),
            "distinct_from_stable_supply_growth": bool(
                abs(independence.get("corr_tvl_dlog7_vs_stable_dlog7") or 0.0) < 0.7
            ),
            "note": "Characterization only. No LEDA promotion.",
        },
        "improves_understanding_without_edge": True,
        "promotion": "not_applicable — market property characterization only",
        "leda_candidate": False,
        "leda_note": "Pre-reg risk/state only if independence from stable supply holds",
    }
