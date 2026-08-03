#!/usr/bin/env python3
"""NEW angle: trend quality — slow trend + not extended + rising breadth proxy (vol ok)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d


def main() -> int:
    df = load_btc_1d()
    # distance from sma as extension
    ext50 = (df["close"] / df["sma_50"] - 1.0).shift(1)
    ext200 = (df["close"] / df["sma_200"] - 1.0).shift(1)
    rv = df["close"].pct_change().rolling(20).std().shift(1)
    rv_med = rv.expanding(60).median()
    # stack: price > sma50 > sma200
    stack = (
        (df["close"].shift(1) > df["sma_50"].shift(1))
        & (df["sma_50"].shift(1) > df["sma_200"].shift(1))
    )
    rules = {
        "stack_not_ext": (stack & (ext50 < 0.15)).astype(float),
        "stack_quiet": (stack & (rv < rv_med)).astype(float),
        "sma200_not_ext200": (
            (df["above_sma_200"] == 1) & (ext200 < 0.25) & (rv < rv_med * 1.2)
        ).astype(float),
        "pullback_to_sma50": (
            (df["above_sma_200"] == 1)
            & (ext50 > -0.02)
            & (ext50 < 0.02)
            & (df["close"].shift(1) > df["close"].shift(10))
        ).astype(float),
    }
    eval_long_flat_rules("ms_trend_quality_v2", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
