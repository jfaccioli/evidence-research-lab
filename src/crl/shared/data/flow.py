"""Point-in-time exchange-flow / large-transfer features (whale/flow programme).

Join rule (programme lock — docs/PROGRAMME_FLOW_WHALE_V1.md):
  For bar decision time t_close, use the last flow observation with
  flow_time <= t_close. Signal on closed bar t → trade at open t+1
  (enforced by engine, not here).

``net_flow`` sign convention: positive = net into exchanges (often risk-off
narrative); negative = net off exchanges. Scientific claims are tested, not assumed.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd


class FlowPITError(ValueError):
    """Flow series or join failed (fail closed)."""


def validate_flow_events(
    events: pd.DataFrame,
    *,
    allow_nan_flow: bool = False,
) -> pd.DataFrame:
    """Require flow_time (UTC), net_flow; sort; reject dups."""
    if events is None or events.empty:
        raise FlowPITError("flow events empty")
    df = events.copy()
    if "flow_time" not in df.columns or "net_flow" not in df.columns:
        raise FlowPITError("flow events require flow_time and net_flow")
    df["flow_time"] = pd.to_datetime(df["flow_time"], utc=True)
    df["net_flow"] = pd.to_numeric(df["net_flow"], errors="coerce")
    if not allow_nan_flow and df["net_flow"].isna().any():
        raise FlowPITError("net_flow contains non-numeric values")
    if allow_nan_flow and df["net_flow"].notna().sum() == 0:
        raise FlowPITError("net_flow all missing")
    df = df.sort_values("flow_time")
    if df["flow_time"].duplicated().any():
        raise FlowPITError("duplicate flow_time values")
    if not df["flow_time"].is_monotonic_increasing:
        raise FlowPITError("flow_time must be monotonic increasing")
    return df.reset_index(drop=True)


def flow_events_content_hash(events: pd.DataFrame) -> str:
    df = validate_flow_events(events)
    payload = df[["flow_time", "net_flow"]].copy()
    payload["flow_time"] = payload["flow_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    raw = payload.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def asof_flow_at_bar_close(
    bar_index: pd.DatetimeIndex,
    events: pd.DataFrame,
    *,
    allow_nan_flow: bool = False,
) -> pd.DataFrame:
    """Right-asof join: each bar close gets last flow_time <= bar timestamp."""
    ev = validate_flow_events(events, allow_nan_flow=allow_nan_flow)
    if not isinstance(bar_index, pd.DatetimeIndex):
        raise FlowPITError("bar_index must be DatetimeIndex")
    bars = (
        bar_index.tz_convert("UTC")
        if bar_index.tz is not None
        else bar_index.tz_localize("UTC")
    )
    bars = pd.to_datetime(bars, utc=True).as_unit("ns")
    left = pd.DataFrame({"bar_close": bars}).sort_values("bar_close")
    right = ev.rename(
        columns={"flow_time": "flow_time_used", "net_flow": "flow_last"}
    ).copy()
    right["flow_time_used"] = pd.DatetimeIndex(
        pd.to_datetime(right["flow_time_used"], utc=True)
    ).as_unit("ns")
    merged = pd.merge_asof(
        left,
        right,
        left_on="bar_close",
        right_on="flow_time_used",
        direction="backward",
    )
    merged = merged.set_index("bar_close")
    out = merged.reindex(bars)
    out.index = bar_index
    return out[["flow_last", "flow_time_used"]]


def add_flow_features(
    ohlcv: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Attach PIT flow features to an OHLCV frame (index = bar close times)."""
    if ohlcv.empty:
        raise FlowPITError("ohlcv empty")
    out = ohlcv.copy()
    asof = asof_flow_at_bar_close(out.index, events)
    out["flow_last"] = asof["flow_last"]
    out["flow_time_used"] = asof["flow_time_used"]

    fl = out["flow_last"]
    out["flow_chg_1"] = fl.diff()
    out["flow_into_exch"] = (fl > 0).astype(float)
    out["flow_off_exch"] = (fl < 0).astype(float)
    med = fl.expanding(min_periods=20).median()
    out["flow_high"] = (fl > med).astype(float)
    out["flow_low"] = (fl < med).astype(float)
    mu = fl.rolling(60, min_periods=30).mean()
    sd = fl.rolling(60, min_periods=30).std()
    out["flow_z_60"] = (fl - mu) / sd.replace(0, np.nan)
    # Extreme inflow / outflow flags (causal expanding quantiles)
    q80 = fl.expanding(min_periods=60).quantile(0.8)
    q20 = fl.expanding(min_periods=60).quantile(0.2)
    out["flow_inflow_extreme"] = (fl > q80).astype(float)
    out["flow_outflow_extreme"] = (fl < q20).astype(float)
    return out


def assert_flow_no_lookahead(
    ohlcv_with_flow: pd.DataFrame,
    events: pd.DataFrame,
    *,
    sample: int = 50,
) -> None:
    validate_flow_events(events)
    df = ohlcv_with_flow
    if "flow_time_used" not in df.columns:
        raise FlowPITError("missing flow_time_used")
    idx = df.index
    bars = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
    n = min(sample, len(df))
    for i in range(n):
        used = df["flow_time_used"].iloc[i]
        if pd.isna(used):
            continue
        if pd.Timestamp(used).tz_convert("UTC") > pd.Timestamp(bars[i]):
            raise AssertionError(
                f"look-ahead flow at i={i}: used={used} bar={bars[i]}"
            )
