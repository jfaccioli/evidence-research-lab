"""Point-in-time open interest (OI) join and causal OI features.

Join rule (programme lock — docs/PROGRAMME_OI_PIT_V1.md):
  For bar decision time t_close, use the last OI snapshot with
  oi_time <= t_close. Signal on closed bar t → trade at open t+1
  (enforced by engine, not here).
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd


class OIPITError(ValueError):
    """OI series or join failed (fail closed)."""


def validate_oi_events(
    events: pd.DataFrame,
    *,
    allow_nan_oi: bool = False,
) -> pd.DataFrame:
    """Require columns oi_time (UTC), open_interest; sort; reject dups."""
    if events is None or events.empty:
        raise OIPITError("oi events empty")
    df = events.copy()
    if "oi_time" not in df.columns or "open_interest" not in df.columns:
        raise OIPITError("oi events require oi_time and open_interest")
    df["oi_time"] = pd.to_datetime(df["oi_time"], utc=True)
    df["open_interest"] = pd.to_numeric(df["open_interest"], errors="coerce")
    if not allow_nan_oi and df["open_interest"].isna().any():
        raise OIPITError("open_interest contains non-numeric values")
    if allow_nan_oi and df["open_interest"].notna().sum() == 0:
        raise OIPITError("open_interest all missing")
    if (df["open_interest"].dropna() < 0).any():
        raise OIPITError("open_interest must be non-negative")
    df = df.sort_values("oi_time")
    if df["oi_time"].duplicated().any():
        raise OIPITError("duplicate oi_time values")
    if not df["oi_time"].is_monotonic_increasing:
        raise OIPITError("oi_time must be monotonic increasing")
    return df.reset_index(drop=True)


def oi_events_content_hash(events: pd.DataFrame) -> str:
    """Deterministic SHA-256 over sorted event table."""
    df = validate_oi_events(events)
    payload = df[["oi_time", "open_interest"]].copy()
    payload["oi_time"] = payload["oi_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    raw = payload.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def asof_oi_at_bar_close(
    bar_index: pd.DatetimeIndex,
    events: pd.DataFrame,
    *,
    allow_nan_oi: bool = False,
) -> pd.DataFrame:
    """Right-asof join: each bar close gets last oi_time <= bar timestamp.

    Returns DataFrame indexed like ``bar_index`` with columns:
    oi_last, oi_time_used (nullable).
    """
    ev = validate_oi_events(events, allow_nan_oi=allow_nan_oi)
    if not isinstance(bar_index, pd.DatetimeIndex):
        raise OIPITError("bar_index must be DatetimeIndex")
    bars = (
        bar_index.tz_convert("UTC")
        if bar_index.tz is not None
        else bar_index.tz_localize("UTC")
    )
    bars = pd.to_datetime(bars, utc=True).as_unit("ns")
    left = pd.DataFrame({"bar_close": bars}).sort_values("bar_close")
    right = ev.rename(
        columns={"oi_time": "oi_time_used", "open_interest": "oi_last"}
    ).copy()
    right["oi_time_used"] = pd.DatetimeIndex(
        pd.to_datetime(right["oi_time_used"], utc=True)
    ).as_unit("ns")
    merged = pd.merge_asof(
        left,
        right,
        left_on="bar_close",
        right_on="oi_time_used",
        direction="backward",
    )
    merged = merged.set_index("bar_close")
    out = merged.reindex(bars)
    out.index = bar_index
    return out[["oi_last", "oi_time_used"]]


def add_oi_features(
    ohlcv: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Attach PIT OI features to an OHLCV frame (index = bar close times)."""
    if ohlcv.empty:
        raise OIPITError("ohlcv empty")
    out = ohlcv.copy()
    asof = asof_oi_at_bar_close(out.index, events)
    out["oi_last"] = asof["oi_last"]
    out["oi_time_used"] = asof["oi_time_used"]

    # Daily (bar-space) changes from the as-of path — causal, past-only.
    oi = out["oi_last"]
    out["oi_chg_1d"] = oi.diff()
    out["oi_chg_pct_1d"] = oi.pct_change()
    out["oi_rising"] = (out["oi_chg_1d"] > 0).astype(float)
    out["oi_falling"] = (out["oi_chg_1d"] < 0).astype(float)
    out["oi_sum_chg_5d"] = out["oi_chg_1d"].rolling(5, min_periods=3).sum()

    med = oi.expanding(min_periods=20).median()
    out["oi_high"] = (oi > med).astype(float)
    out["oi_low"] = (oi < med).astype(float)

    mu = oi.rolling(60, min_periods=30).mean()
    sd = oi.rolling(60, min_periods=30).std()
    out["oi_z_60"] = (oi - mu) / sd.replace(0, np.nan)

    # Fixed causal 80% expanding quantile of oi_chg_pct (programme lock — one threshold).
    chg_pct = out["oi_chg_pct_1d"]
    q80 = chg_pct.expanding(min_periods=60).quantile(0.8)
    out["oi_chg_pct_high"] = (chg_pct > q80).astype(float)

    # Multi-day OI build high flag: above expanding median of oi_sum_chg_5d.
    s5 = out["oi_sum_chg_5d"]
    s_med = s5.expanding(min_periods=20).median()
    out["oi_sum5_high"] = (s5 > s_med).astype(float)

    return out


def assert_oi_no_lookahead(
    ohlcv_with_oi: pd.DataFrame,
    events: pd.DataFrame,
    *,
    sample: int = 50,
) -> None:
    """Sanity: oi_time_used at bar i must be <= bar timestamp i."""
    validate_oi_events(events)
    df = ohlcv_with_oi
    if "oi_time_used" not in df.columns:
        raise OIPITError("missing oi_time_used")
    idx = df.index
    bars = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
    n = min(sample, len(df))
    for i in range(n):
        used = df["oi_time_used"].iloc[i]
        if pd.isna(used):
            continue
        if pd.Timestamp(used).tz_convert("UTC") > pd.Timestamp(bars[i]):
            raise AssertionError(
                f"look-ahead oi at i={i}: used={used} bar={bars[i]}"
            )
