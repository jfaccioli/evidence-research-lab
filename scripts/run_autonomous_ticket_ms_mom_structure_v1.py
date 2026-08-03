#!/usr/bin/env python3
"""Momentum + structure: intermediate mom with funding/vol guards (not pure mom clone)."""
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
    funding = pd.read_parquet(
        project_root()
        / "data/processed/funding/binance_funding_BTCUSDT_funding_d1bbe1f63b23.parquet"
    )
    fl = asof_funding_rate(df.index, funding).shift(1)
    fz = (fl - fl.rolling(60, min_periods=30).mean()) / fl.rolling(60, min_periods=30).std().replace(
        0, float("nan")
    )
    mom20 = df["close"].pct_change(20).shift(1)
    mom60 = df["close"].pct_change(60).shift(1)
    rv = df["close"].pct_change().rolling(20).std().shift(1)
    rv_med = rv.expanding(60).median()
    rules = {
        "mom20_trend_fund_ok": (
            (mom20 > 0) & (df["above_sma_200"] == 1) & (fz < 1.0)
        ).astype(float),
        "mom60_quiet": ((mom60 > 0) & (rv < rv_med) & (df["above_sma_50"] == 1)).astype(float),
        "mom20_not_crowded": ((mom20 > 0) & (fz < 0) & (df["above_sma_50"] == 1)).astype(float),
        "dual_mom_trend": (
            (mom20 > 0) & (mom60 > 0) & (df["above_sma_200"] == 1)
        ).astype(float),
    }
    eval_long_flat_rules("ms_mom_structure_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
