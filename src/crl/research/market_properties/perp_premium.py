"""Market property: perpetual premium (mark–index deviation).

What it measures
----------------
Binance USDT-M ``premiumIndex`` kline close: a continuous measure of how far
perpetual mark price sits from the index (spot basket). Related to funding
*equilibrium* but is a **level process**, not the discrete 8h funding print.

Putative mechanism
------------------
Leverage demand / inventory pressure in perps: longs pay shorts when premium
is high (and vice versa). Distinct from spot OHLCV path and from lagged RV.

Characterization only — not a trading rule. LEDA only after pre-reg.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.shared.data.premium import validate_premium_events

PROPERTY_ID = "perp_premium"
PROPERTY_VERSION = 1


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 20:
        return None
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return None
    v = float(np.corrcoef(a, b)[0, 1])
    return None if v != v else round(v, 6)


def align_premium_to_ohlcv(
    ohlcv: pd.DataFrame,
    premium_events: pd.DataFrame,
) -> pd.DataFrame:
    """PIT as-of join: last premium event_time ≤ bar timestamp (UTC)."""
    ev = validate_premium_events(premium_events)
    bars = (
        ohlcv.index.tz_convert("UTC")
        if ohlcv.index.tz is not None
        else ohlcv.index.tz_localize("UTC")
    )
    bars = pd.to_datetime(bars, utc=True)
    left = pd.DataFrame({"bar_ts": bars}).sort_values("bar_ts")
    right = ev.rename(columns={"event_time": "prem_time", "premium_close": "premium"})
    right["prem_time"] = pd.to_datetime(right["prem_time"], utc=True)
    right = right.sort_values("prem_time")
    merged = pd.merge_asof(
        left, right, left_on="bar_ts", right_on="prem_time", direction="backward"
    )
    merged = merged.set_index("bar_ts")
    # restore original index labels
    premium = merged["premium"].to_numpy()
    close = ohlcv["close"].astype(float)
    log_ret = np.log(close / close.shift(1))
    rv_end = log_ret.rolling(20, min_periods=20).std()

    prem = pd.Series(premium, index=ohlcv.index, dtype=float)
    # Strict lag for predictive association: known through prior bar
    prem_lag = prem.shift(1)

    out = pd.DataFrame(
        {
            "premium": prem.to_numpy(),
            "premium_lag": prem_lag.to_numpy(),
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
    return out


def _align_funding_daily(
    ohlcv: pd.DataFrame, funding_events: pd.DataFrame
) -> pd.Series:
    """Last funding_rate with funding_time ≤ bar ts."""
    fe = funding_events.copy()
    fe["funding_time"] = pd.to_datetime(fe["funding_time"], utc=True)
    fe["funding_rate"] = pd.to_numeric(fe["funding_rate"], errors="coerce")
    fe = fe.dropna(subset=["funding_rate"]).sort_values("funding_time")
    bars = (
        ohlcv.index.tz_convert("UTC")
        if ohlcv.index.tz is not None
        else ohlcv.index.tz_localize("UTC")
    )
    left = pd.DataFrame({"bar_ts": pd.to_datetime(bars, utc=True)}).sort_values("bar_ts")
    right = fe.rename(columns={"funding_time": "ft", "funding_rate": "fr"})
    m = pd.merge_asof(left, right, left_on="bar_ts", right_on="ft", direction="backward")
    return pd.Series(m["fr"].to_numpy(), index=ohlcv.index, dtype=float)


def characterize_perp_premium(
    ohlcv: pd.DataFrame,
    premium_events: pd.DataFrame,
    *,
    funding_events: Optional[pd.DataFrame] = None,
    aggression: Optional[pd.DataFrame] = None,
    min_points: int = 100,
) -> dict[str, Any]:
    """Characterize perpetual premium as a market property (not a trade map)."""
    frame = align_premium_to_ohlcv(ohlcv, premium_events)
    if funding_events is not None and len(funding_events):
        frame["funding_lag"] = _align_funding_daily(ohlcv, funding_events).shift(1)
    if aggression is not None and "taker_buy_ratio_lag" in aggression.columns:
        frame["tbr_lag"] = aggression["taker_buy_ratio_lag"]
        frame["intensity_lag"] = aggression.get("trade_intensity_lag")

    need = ["premium_lag", "ret_lag", "rv_lag", "rv_next", "fwd_ret"]
    df = frame.dropna(subset=need)
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "property_id": PROPERTY_ID,
            "n": n,
            "reason": f"need >= {min_points} aligned bars",
        }

    p = df["premium_lag"].to_numpy(dtype=float)
    ret_l = df["ret_lag"].to_numpy(dtype=float)
    rv_l = df["rv_lag"].to_numpy(dtype=float)
    rv_n = df["rv_next"].to_numpy(dtype=float)
    fwd = df["fwd_ret"].to_numpy(dtype=float)

    # Persistence of the property itself
    prem_raw = frame["premium"].dropna()
    if len(prem_raw) > 30:
        ac1 = _safe_corr(
            prem_raw.iloc[:-1].to_numpy(dtype=float),
            prem_raw.iloc[1:].to_numpy(dtype=float),
        )
    else:
        ac1 = None

    independence: dict[str, Any] = {
        "corr_premium_lag_vs_ret_lag": _safe_corr(p, ret_l),
        "corr_premium_lag_vs_rv_lag": _safe_corr(p, rv_l),
    }
    if "funding_lag" in df.columns:
        fl = df["funding_lag"].to_numpy(dtype=float)
        mask = np.isfinite(fl)
        independence["corr_premium_lag_vs_funding_lag"] = _safe_corr(p[mask], fl[mask])
        independence["n_with_funding"] = int(mask.sum())
    if "tbr_lag" in df.columns:
        tbr = df["tbr_lag"].to_numpy(dtype=float)
        mask = np.isfinite(tbr)
        independence["corr_premium_lag_vs_tbr_lag"] = _safe_corr(p[mask], tbr[mask])

    skill = {
        "corr_premium_lag_vs_fwd_ret": _safe_corr(p, fwd),
        "corr_premium_lag_vs_rv_next": _safe_corr(p, rv_n),
        "autocorr_premium_lag1": ac1,
    }

    abs_dir = abs(skill["corr_premium_lag_vs_fwd_ret"] or 0.0)
    abs_unc = abs(skill["corr_premium_lag_vs_rv_next"] or 0.0)
    abs_fund = abs(independence.get("corr_premium_lag_vs_funding_lag") or 0.0)

    # Regime-ish: high |premium| vs next RV
    abs_p = np.abs(p)
    high = abs_p >= np.nanpercentile(abs_p, 80)
    mean_rv_hi = float(np.mean(rv_n[high])) if high.any() else float("nan")
    mean_rv_lo = float(np.mean(rv_n[~high])) if (~high).any() else float("nan")
    mean_fwd_hi = float(np.mean(fwd[high])) if high.any() else float("nan")

    coverage = {
        "n_bars_ohlcv": len(ohlcv),
        "n_premium_events": len(premium_events),
        "n_aligned": n,
        "premium_mean": round(float(np.mean(p)), 8),
        "premium_std": round(float(np.std(p, ddof=1)), 8),
        "premium_abs_p80": round(float(np.nanpercentile(abs_p, 80)), 8),
    }

    # Role classification (descriptive)
    if abs_fund > 0.7:
        independence_note = "Highly collinear with funding — limited new information"
    elif abs_fund > 0.4:
        independence_note = "Moderately related to funding; residual may still be informative"
    else:
        independence_note = "Materially distinct from funding on this sample"

    if abs_unc > abs_dir + 0.02:
        role = "uncertainty / leverage-stress more than direction"
    elif abs_dir > abs_unc + 0.02:
        role = "direction more than uncertainty"
    else:
        role = "weak linear association with both direction and next RV"

    return {
        "ok": True,
        "property_id": PROPERTY_ID,
        "version": PROPERTY_VERSION,
        "what_it_measures": (
            "USDT-M perpetual premium index (mark vs index deviation) over each bar"
        ),
        "putative_mechanism": (
            "Futures leverage demand / inventory imbalance; related to funding "
            "equilibrium but continuous level, not 8h print"
        ),
        "primary_role_guess": role,
        "coverage": coverage,
        "independence_vs_known_properties": independence,
        "independence_note": independence_note,
        "association_next_state": skill,
        "conditional": {
            "mean_rv_next_when_abs_premium_ge_p80": (
                round(mean_rv_hi, 8) if mean_rv_hi == mean_rv_hi else None
            ),
            "mean_rv_next_when_abs_premium_lt_p80": (
                round(mean_rv_lo, 8) if mean_rv_lo == mean_rv_lo else None
            ),
            "mean_fwd_ret_when_abs_premium_ge_p80": (
                round(mean_fwd_hi, 8) if mean_fwd_hi == mean_fwd_hi else None
            ),
        },
        "interpretation": {
            "more_about_uncertainty_than_direction": bool(abs_unc > abs_dir + 0.02),
            "distinct_from_funding": bool(abs_fund < 0.7),
            "persistent_level_process": bool(ac1 is not None and ac1 > 0.3),
            "note": (
                "Descriptive only. Improves scientific description of futures "
                "state even if never a trade edge. No LEDA promotion here."
            ),
        },
        "improves_understanding_without_edge": True,
        "promotion": "not_applicable — market property characterization only",
        "leda_candidate": False,
        "leda_note": (
            "Candidate for risk/state channel only after pre-reg claim and "
            "residualization vs funding if collinear"
        ),
        "next_science": (
            "If collinear with funding, study premium residual after funding; "
            "if independent, pre-reg risk evidence — never atomistic long/flat fishing"
        ),
    }
