"""Causal feature engineering — no full-sample quantiles, no future peek."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add Phase-1 features using only past/current bar data.

    Rolling windows end at t. Distributional thresholds use expanding
    (causal) statistics — never full-sample medians/quantiles.
    """
    out = df.copy()
    c = out["close"].astype(float)
    v = out["volume"].astype(float)
    idx = out.index

    out["ret_1"] = c.pct_change()
    out["log_ret_1"] = np.log(c / c.shift(1))

    # Multi-horizon simple returns (momentum / mean-reversion building blocks)
    for w in (3, 5, 10, 20, 30, 60, 90):
        out[f"ret_{w}"] = c.pct_change(w)

    # Momentum acceleration (causal): short mom minus long mom
    out["mom_accel_20_60"] = out["ret_20"] - out["ret_60"]
    out["mom_accel_10_30"] = out["ret_10"] - out["ret_30"]

    for w in (10, 20, 50, 100, 200):
        out[f"sma_{w}"] = c.rolling(w, min_periods=w).mean()
        out[f"ema_{w}"] = c.ewm(span=w, adjust=False, min_periods=w).mean()

    # Distance from SMAs (mean reversion / stretch)
    for w in (20, 50, 200):
        out[f"dist_sma_{w}"] = c / out[f"sma_{w}"] - 1.0

    # Rolling price z-score (causal)
    for w in (20, 60):
        mu = c.rolling(w, min_periods=w).mean()
        sd = c.rolling(w, min_periods=w).std()
        out[f"price_z_{w}"] = (c - mu) / sd.replace(0, np.nan)

    # Realized vol
    out["rvol_20"] = out["log_ret_1"].rolling(20, min_periods=20).std() * np.sqrt(365)
    out["rvol_60"] = out["log_ret_1"].rolling(60, min_periods=60).std() * np.sqrt(365)
    out["rvol_20_exp_median"] = out["rvol_20"].expanding(min_periods=20).median()
    out["rvol_below_median"] = (out["rvol_20"] < out["rvol_20_exp_median"]).astype(float)
    out["rvol_above_median"] = (out["rvol_20"] >= out["rvol_20_exp_median"]).astype(float)
    # Vol of vol / change
    out["rvol_20_chg"] = out["rvol_20"].pct_change(5)

    # ATR
    prev_c = c.shift(1)
    tr = pd.concat(
        [
            (out["high"] - out["low"]).abs(),
            (out["high"] - prev_c).abs(),
            (out["low"] - prev_c).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr_14"] = tr.rolling(14, min_periods=14).mean()
    out["atr_pct"] = out["atr_14"] / c

    # Volume
    for w in (20, 60):
        vol_mean = v.rolling(w, min_periods=w).mean()
        vol_std = v.rolling(w, min_periods=w).std()
        out[f"vol_z_{w}"] = (v - vol_mean) / vol_std.replace(0, np.nan)
    out["vol_sma_20"] = v.rolling(20, min_periods=20).mean()
    out["vol_ratio_20"] = v / out["vol_sma_20"]

    # Trend flags
    out["above_sma_200"] = (c > out["sma_200"]).astype(float)
    out["above_sma_50"] = (c > out["sma_50"]).astype(float)
    out["above_sma_20"] = (c > out["sma_20"]).astype(float)
    out["sma_50_above_200"] = (out["sma_50"] > out["sma_200"]).astype(float)
    out["sma_20_above_50"] = (out["sma_20"] > out["sma_50"]).astype(float)

    # Momentum flags
    out["mom_pos_20"] = (out["ret_20"] > 0).astype(float)
    out["mom_pos_60"] = (out["ret_60"] > 0).astype(float)

    # Calendar (UTC) — known at bar open for daily; for 4h uses bar timestamp
    if isinstance(idx, pd.DatetimeIndex):
        ts = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
        out["dow"] = ts.dayofweek.astype(float)  # 0=Mon … 6=Sun
        out["dom"] = ts.day.astype(float)
        out["month"] = ts.month.astype(float)
        out["is_weekend"] = (out["dow"] >= 5).astype(float)
        out["is_monday"] = (out["dow"] == 0).astype(float)
        out["is_friday"] = (out["dow"] == 4).astype(float)
        out["is_month_start"] = (out["dom"] <= 3).astype(float)
        out["is_month_end"] = (out["dom"] >= 28).astype(float)
        if hasattr(ts, "hour"):
            out["hour_utc"] = ts.hour.astype(float)
        else:
            out["hour_utc"] = 0.0

    # Donchian-style channel (causal rolling max/min of prior highs/lows)
    # Use shift(1) so breakout at t does not use t's high/low as both signal and barrier
    for w in (20, 55, 100):
        out[f"donch_high_{w}"] = out["high"].astype(float).shift(1).rolling(w, min_periods=w).max()
        out[f"donch_low_{w}"] = out["low"].astype(float).shift(1).rolling(w, min_periods=w).min()
        out[f"above_donch_{w}"] = (c > out[f"donch_high_{w}"]).astype(float)
        out[f"below_donch_{w}"] = (c < out[f"donch_low_{w}"]).astype(float)

    # ATR trailing-style: close vs close - k*ATR (long filter)
    out["close_minus_2atr"] = c - 2.0 * out["atr_14"]
    out["above_atr_trail"] = (c > out["close_minus_2atr"].shift(1)).astype(float)

    # Optional external columns (funding, etc.) left as-is if present.
    # True funding features must be joined via crl.shared.data.funding.add_funding_features
    # (PIT as-of bar close) before/after this call — never invent future funding here.
    # Sentiment/on-chain: only if joined with trust-scored PIT series

    return out


def assert_no_lookahead_sma(df: pd.DataFrame, window: int = 200) -> None:
    """Sanity: SMA at t must equal mean of close[t-window+1:t+1]."""
    col = f"sma_{window}"
    if col not in df.columns:
        return
    c = df["close"].astype(float)
    for i in range(window - 1, min(window + 50, len(df))):
        expected = c.iloc[i - window + 1 : i + 1].mean()
        got = df[col].iloc[i]
        if np.isnan(got):
            continue
        if not np.isclose(got, expected, rtol=1e-9, atol=1e-9):
            raise AssertionError(f"Look-ahead or SMA bug at i={i}: {got} vs {expected}")
