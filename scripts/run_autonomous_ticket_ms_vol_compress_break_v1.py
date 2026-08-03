#!/usr/bin/env python3
"""NEW angle: vol compression then expansion + trend (breakout-from-quiet)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d


def main() -> int:
    df = load_btc_1d()
    rv = df["close"].pct_change().rolling(20).std()
    rv_lag = rv.shift(1)
    rv_min = rv_lag.rolling(60, min_periods=30).min()
    # compression: near 60d low vol
    compress = rv_lag <= (rv_min * 1.15)
    # expansion: rv rising vs 5d ago
    expand = rv_lag > rv_lag.shift(5)
    ret20 = df["close"].pct_change(20).shift(1)
    rules = {
        "quiet_then_expand_trend": (
            compress.shift(5).fillna(False) & expand & (df["above_sma_50"] == 1)
        ).astype(float),
        "compress_only_trend": (compress & (df["above_sma_200"] == 1)).astype(float),
        "expand_from_quiet_mom": (
            compress.shift(5).fillna(False) & expand & (ret20 > 0)
        ).astype(float),
        "not_high_vol_trend": (
            (rv_lag < rv_lag.expanding(60).median()) & (df["above_sma_50"] == 1)
        ).astype(float),
    }
    eval_long_flat_rules("ms_vol_compress_break_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
