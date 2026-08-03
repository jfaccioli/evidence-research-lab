#!/usr/bin/env python3
"""NEW angle: re-enter long after controlled drawdown from peak (not panic)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d


def main() -> int:
    df = load_btc_1d()
    peak = df["close"].cummax()
    dd = (df["close"] / peak - 1.0).shift(1)
    # recovery: dd was deep, now improving
    dd_prev = dd.shift(5)
    improving = dd > dd_prev
    rules = {
        "dd_10_20_trend": (
            (dd <= -0.10) & (dd >= -0.20) & (df["above_sma_50"] == 1)
        ).astype(float),
        "dd_recover_5d": (
            (dd_prev <= -0.15) & improving & (df["above_sma_200"] == 1)
        ).astype(float),
        "shallow_dd_hold": ((dd > -0.10) & (df["above_sma_200"] == 1)).astype(float),
        "dd_15_bounce": (
            (dd <= -0.15) & (df["close"] > df["close"].shift(3)) & (df["above_sma_50"] == 1)
        ).astype(float),
    }
    # shift close comparison already causal if using shift on price in expression — close>close.shift(3) uses current close; need lag
    rules["dd_15_bounce"] = (
        (dd <= -0.15)
        & (df["close"].shift(1) > df["close"].shift(4))
        & (df["above_sma_50"] == 1)
    ).astype(float)
    eval_long_flat_rules("ms_dd_reentry_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
