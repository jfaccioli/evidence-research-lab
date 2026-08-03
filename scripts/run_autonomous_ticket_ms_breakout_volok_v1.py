#!/usr/bin/env python3
"""Donchian-style breakout with vol and funding guards (daily)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from crl.research.market_structure.funding_carry import asof_funding_rate
from crl.shared.config import project_root
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d


def main() -> int:
    df = load_btc_1d()
    hi20 = df["high"].rolling(20).max().shift(1)
    hi55 = df["high"].rolling(55).max().shift(1)
    close_lag = df["close"].shift(1)
    brk20 = close_lag >= hi20
    brk55 = close_lag >= hi55
    rv = df["close"].pct_change().rolling(20).std().shift(1)
    rv_med = rv.expanding(60).median()
    funding = pd.read_parquet(
        project_root()
        / "data/processed/funding/binance_funding_BTCUSDT_funding_d1bbe1f63b23.parquet"
    )
    fl = asof_funding_rate(df.index, funding).shift(1)
    fz = (fl - fl.rolling(60, min_periods=30).mean()) / fl.rolling(60, min_periods=30).std().replace(
        0, float("nan")
    )
    rules = {
        "donch20_quiet": (brk20 & (rv < rv_med * 1.2) & (df["above_sma_50"] == 1)).astype(float),
        "donch55_trend": (brk55 & (df["above_sma_200"] == 1)).astype(float),
        "donch20_fund_ok": (brk20 & (fz < 1.0) & (df["above_sma_50"] == 1)).astype(float),
        "donch55_quiet_fund": (
            brk55 & (rv < rv_med) & (fz < 0.5) & (df["above_sma_200"] == 1)
        ).astype(float),
    }
    eval_long_flat_rules("ms_breakout_volok_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
