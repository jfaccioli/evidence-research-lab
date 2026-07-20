"""Causal regime labels: trend × volatility 2×2."""

from __future__ import annotations

import pandas as pd


def add_regime_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Label each bar with bull/bear × high/low vol using past-only features.

    Requires features from `add_features`: sma_200, rvol_20, rvol_20_exp_median.
    """
    out = df.copy()
    bull = out["close"] > out["sma_200"]
    high_vol = out["rvol_20"] >= out["rvol_20_exp_median"]

    regime = pd.Series("unknown", index=out.index, dtype=object)
    known = out["sma_200"].notna() & out["rvol_20"].notna() & out["rvol_20_exp_median"].notna()
    regime.loc[known & bull & ~high_vol] = "bull_low_vol"
    regime.loc[known & bull & high_vol] = "bull_high_vol"
    regime.loc[known & ~bull & ~high_vol] = "bear_low_vol"
    regime.loc[known & ~bull & high_vol] = "bear_high_vol"
    out["regime"] = regime
    return out


def regime_concentration(trade_regimes: list[str], trade_returns: list[float]) -> dict:
    """Share of positive excess contribution by regime cell."""
    cells = ["bull_low_vol", "bull_high_vol", "bear_low_vol", "bear_high_vol"]
    contrib = {c: 0.0 for c in cells}
    for reg, ret in zip(trade_regimes, trade_returns):
        if reg in contrib:
            # use max(ret,0) contribution of signed returns sum abs
            contrib[reg] += ret
    total_pos = sum(v for v in contrib.values() if v > 0)
    total_abs = sum(abs(v) for v in contrib.values()) or 1.0
    shares = {k: (max(v, 0.0) / total_pos if total_pos > 0 else 0.0) for k, v in contrib.items()}
    max_share = max(shares.values()) if shares else 0.0
    return {
        "contrib": contrib,
        "pos_shares": shares,
        "max_pos_share": max_share,
        "total_abs_contrib": total_abs,
    }
