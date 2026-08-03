#!/usr/bin/env python3
"""NEW angle: funding *change* (acceleration), not level — long when crowding eases."""
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
    chg = fl.diff()
    chg_z = (chg - chg.rolling(60, min_periods=30).mean()) / chg.rolling(
        60, min_periods=30
    ).std().replace(0, float("nan"))
    rules = {
        "fund_falling_trend": ((chg < 0) & (df["above_sma_50"] == 1)).astype(float),
        "fund_chg_z_neg_trend": ((chg_z < 0) & (df["above_sma_200"] == 1)).astype(float),
        "trend_unless_fund_accel": (
            (df["above_sma_200"] == 1) & (chg_z < 1.0)
        ).astype(float),
        "fund_falling_while_pos": ((chg < 0) & (fl > 0) & (df["above_sma_50"] == 1)).astype(
            float
        ),
    }
    eval_long_flat_rules("ms_funding_chg_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
