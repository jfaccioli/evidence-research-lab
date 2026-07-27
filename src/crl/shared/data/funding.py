"""Point-in-time funding rate join and causal funding features.

Join rule (programme lock):
  For bar decision time t_close, use the last funding event with
  funding_time <= t_close. Signal on closed bar t → trade at open t+1
  (enforced by engine, not here).
"""

from __future__ import annotations

import hashlib
from typing import Optional

import numpy as np
import pandas as pd


class FundingPITError(ValueError):
    """Funding series or join failed (fail closed)."""


def validate_funding_events(
    events: pd.DataFrame,
    *,
    allow_nan_rate: bool = False,
) -> pd.DataFrame:
    """Require columns funding_time (UTC), funding_rate; sort; reject dups."""
    if events is None or events.empty:
        raise FundingPITError("funding events empty")
    df = events.copy()
    if "funding_time" not in df.columns or "funding_rate" not in df.columns:
        raise FundingPITError("funding events require funding_time and funding_rate")
    df["funding_time"] = pd.to_datetime(df["funding_time"], utc=True)
    df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
    if not allow_nan_rate and df["funding_rate"].isna().any():
        raise FundingPITError("funding_rate contains non-numeric values")
    if allow_nan_rate and df["funding_rate"].notna().sum() == 0:
        raise FundingPITError("funding_rate all missing")
    df = df.sort_values("funding_time")
    if df["funding_time"].duplicated().any():
        raise FundingPITError("duplicate funding_time values")
    if not df["funding_time"].is_monotonic_increasing:
        raise FundingPITError("funding_time must be monotonic increasing")
    return df.reset_index(drop=True)


def funding_events_content_hash(events: pd.DataFrame) -> str:
    """Deterministic SHA-256 over sorted event table."""
    df = validate_funding_events(events)
    payload = df[["funding_time", "funding_rate"]].copy()
    payload["funding_time"] = payload["funding_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    raw = payload.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def asof_funding_at_bar_close(
    bar_index: pd.DatetimeIndex,
    events: pd.DataFrame,
    *,
    allow_nan_rate: bool = False,
) -> pd.DataFrame:
    """Right-asof join: each bar close gets last funding_time <= bar timestamp.

    Returns DataFrame indexed like ``bar_index`` with columns:
    funding_last, funding_time_used (nullable).
    """
    ev = validate_funding_events(events, allow_nan_rate=allow_nan_rate)
    if not isinstance(bar_index, pd.DatetimeIndex):
        raise FundingPITError("bar_index must be DatetimeIndex")
    bars = bar_index.tz_convert("UTC") if bar_index.tz is not None else bar_index.tz_localize("UTC")
    left = pd.DataFrame({"bar_close": bars}).sort_values("bar_close")
    right = ev.rename(columns={"funding_time": "funding_time_used", "funding_rate": "funding_last"})
    # merge_asof requires sorted keys
    merged = pd.merge_asof(
        left,
        right,
        left_on="bar_close",
        right_on="funding_time_used",
        direction="backward",
    )
    merged = merged.set_index("bar_close")
    # Reindex to original order
    out = merged.reindex(bars)
    out.index = bar_index
    return out[["funding_last", "funding_time_used"]]


def trailing_event_sum(
    bar_index: pd.DatetimeIndex,
    events: pd.DataFrame,
    *,
    window: pd.Timedelta,
) -> pd.Series:
    """Sum funding_rate for events in (t_close - window, t_close]."""
    ev = validate_funding_events(events)
    bars = bar_index.tz_convert("UTC") if bar_index.tz is not None else bar_index.tz_localize("UTC")
    times = pd.DatetimeIndex(ev["funding_time"]).tz_convert("UTC")
    rates = ev["funding_rate"].to_numpy(dtype=float)
    sums = np.empty(len(bars), dtype=float)
    j0 = 0
    n = len(times)
    for i, t in enumerate(bars):
        t_ts = pd.Timestamp(t).tz_convert("UTC")
        start = t_ts - window
        while j0 < n and times[j0] <= start:
            j0 += 1
        j1 = j0
        total = 0.0
        while j1 < n and times[j1] <= t_ts:
            total += float(rates[j1])
            j1 += 1
        sums[i] = total if j1 > j0 else np.nan
    return pd.Series(sums, index=bar_index, name="funding_sum_window")


def add_funding_features(
    ohlcv: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Attach PIT funding features to an OHLCV frame (index = bar close times)."""
    if ohlcv.empty:
        raise FundingPITError("ohlcv empty")
    out = ohlcv.copy()
    asof = asof_funding_at_bar_close(out.index, events)
    out["funding_last"] = asof["funding_last"]
    out["funding_time_used"] = asof["funding_time_used"]

    # Event-to-event change known only after the later event's funding_time.
    ev = validate_funding_events(events)
    ev_chg = ev.copy()
    ev_chg["funding_rate"] = ev_chg["funding_rate"].diff()
    chg_asof = asof_funding_at_bar_close(
        out.index, ev_chg, allow_nan_rate=True
    )
    out["funding_chg_1"] = chg_asof["funding_last"]

    out["funding_sum_24h"] = trailing_event_sum(
        out.index, events, window=pd.Timedelta(hours=24)
    )

    # Causal daily features from funding_last path
    fl = out["funding_last"]
    out["funding_pos"] = (fl > 0).astype(float)
    out["funding_neg"] = (fl < 0).astype(float)
    out["funding_zero"] = (fl == 0).astype(float)
    med = fl.expanding(min_periods=20).median()
    out["funding_high"] = (fl > med).astype(float)
    out["funding_low"] = (fl < med).astype(float)
    mu = fl.rolling(60, min_periods=30).mean()
    sd = fl.rolling(60, min_periods=30).std()
    out["funding_z_60"] = (fl - mu) / sd.replace(0, np.nan)
    # 24h sum high flag (causal expanding median)
    s24 = out["funding_sum_24h"]
    s_med = s24.expanding(min_periods=20).median()
    out["funding_sum24_high"] = (s24 > s_med).astype(float)
    return out


def assert_funding_no_lookahead(
    ohlcv_with_funding: pd.DataFrame,
    events: pd.DataFrame,
    *,
    sample: int = 50,
) -> None:
    """Sanity: funding_time_used at bar i must be <= bar timestamp i."""
    ev = validate_funding_events(events)
    df = ohlcv_with_funding
    if "funding_time_used" not in df.columns:
        raise FundingPITError("missing funding_time_used")
    idx = df.index
    bars = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
    n = min(sample, len(df))
    for i in range(n):
        used = df["funding_time_used"].iloc[i]
        if pd.isna(used):
            continue
        if pd.Timestamp(used).tz_convert("UTC") > pd.Timestamp(bars[i]):
            raise AssertionError(
                f"look-ahead funding at i={i}: used={used} bar={bars[i]}"
            )
