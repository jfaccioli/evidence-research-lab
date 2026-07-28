"""Generic daily external series join (PIT as-of bar close).

Used for free third-party daily metrics (e.g. Coinbase premium) that are not
OHLCV. Same join rule as flow: last event_time ≤ bar close; fixed publish lag
at ingest time.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd


class ExternalSeriesError(ValueError):
    pass


def validate_external_events(
    events: pd.DataFrame,
    *,
    time_col: str = "event_time",
    value_col: str = "value",
) -> pd.DataFrame:
    if events is None or events.empty:
        raise ExternalSeriesError("external events empty")
    df = events.copy()
    if time_col not in df.columns or value_col not in df.columns:
        raise ExternalSeriesError(f"need {time_col} and {value_col}")
    df[time_col] = pd.to_datetime(df[time_col], utc=True)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    if df[value_col].isna().all():
        raise ExternalSeriesError("value all missing")
    df = df.sort_values(time_col)
    if df[time_col].duplicated().any():
        raise ExternalSeriesError("duplicate event_time")
    return df.reset_index(drop=True)


def external_events_hash(events: pd.DataFrame) -> str:
    df = validate_external_events(events)
    payload = df[["event_time", "value"]].copy()
    payload["event_time"] = payload["event_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    return hashlib.sha256(payload.to_csv(index=False).encode()).hexdigest()


def add_external_level_features(
    ohlcv: pd.DataFrame,
    events: pd.DataFrame,
    *,
    prefix: str = "xser",
) -> pd.DataFrame:
    """Attach level/z/extreme flags for a single external series."""
    ev = validate_external_events(events)
    out = ohlcv.copy()
    bars = (
        out.index.tz_convert("UTC")
        if out.index.tz is not None
        else out.index.tz_localize("UTC")
    )
    bars = pd.to_datetime(bars, utc=True).as_unit("ns")
    left = pd.DataFrame({"bar_close": bars}).sort_values("bar_close")
    right = ev.rename(columns={"event_time": "t_used", "value": f"{prefix}_last"})
    right["t_used"] = pd.DatetimeIndex(pd.to_datetime(right["t_used"], utc=True)).as_unit(
        "ns"
    )
    merged = pd.merge_asof(
        left, right, left_on="bar_close", right_on="t_used", direction="backward"
    )
    merged = merged.set_index("bar_close").reindex(bars)
    merged.index = out.index
    out[f"{prefix}_last"] = merged[f"{prefix}_last"]
    out[f"{prefix}_time_used"] = merged["t_used"]
    s = out[f"{prefix}_last"]
    out[f"{prefix}_chg_1"] = s.diff()
    out[f"{prefix}_pos"] = (s > 0).astype(float)
    out[f"{prefix}_neg"] = (s < 0).astype(float)
    med = s.expanding(min_periods=20).median()
    out[f"{prefix}_high"] = (s > med).astype(float)
    out[f"{prefix}_low"] = (s < med).astype(float)
    mu = s.rolling(60, min_periods=30).mean()
    sd = s.rolling(60, min_periods=30).std()
    out[f"{prefix}_z_60"] = (s - mu) / sd.replace(0, np.nan)
    q80 = s.expanding(min_periods=60).quantile(0.8)
    q20 = s.expanding(min_periods=60).quantile(0.2)
    out[f"{prefix}_hi_ext"] = (s > q80).astype(float)
    out[f"{prefix}_lo_ext"] = (s < q20).astype(float)
    return out
