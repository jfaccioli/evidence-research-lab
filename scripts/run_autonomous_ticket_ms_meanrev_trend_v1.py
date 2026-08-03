#!/usr/bin/env python3
"""Pullback mean-reversion inside slow uptrend (fade extension, not pure MR)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d


def main() -> int:
    df = load_btc_1d()
    # z-score of price vs sma20
    sma20 = df["close"].rolling(20).mean()
    sd20 = df["close"].rolling(20).std()
    z20 = ((df["close"] - sma20) / sd20.replace(0, float("nan"))).shift(1)
    ext50 = (df["close"] / df["sma_50"] - 1.0).shift(1)
    rules = {
        # buy dip in uptrend: z depressed but above long SMA
        "z_dip_uptrend": ((z20 < -1.0) & (df["above_sma_200"] == 1)).astype(float),
        "z_mild_dip_sma50": ((z20 < -0.5) & (df["above_sma_50"] == 1)).astype(float),
        # avoid extension: long only when not stretched
        "uptrend_not_stretched": (
            (df["above_sma_200"] == 1) & (ext50 < 0.12) & (ext50 > -0.05)
        ).astype(float),
        "deep_dip_recover": (
            (z20.shift(3) < -1.5) & (z20 > z20.shift(3)) & (df["above_sma_200"] == 1)
        ).astype(float),
    }
    eval_long_flat_rules("ms_meanrev_trend_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
