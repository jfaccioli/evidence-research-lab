#!/usr/bin/env python3
"""NEW angle: premium vs funding disagreement (structure tension)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from crl.research.market_structure.funding_carry import asof_funding_rate
from crl.shared.config import project_root
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d


def main() -> int:
    df = load_btc_1d("2019-12-25")
    root = project_root()
    funding = pd.read_parquet(
        root / "data/processed/funding/binance_funding_BTCUSDT_funding_d1bbe1f63b23.parquet"
    )
    prem = pd.read_parquet(
        root / "data/processed/premium/binance_premium_BTCUSDT_premium_1d_5f3bba74d0f0.parquet"
    )
    fl = asof_funding_rate(df.index, funding).shift(1)
    left = pd.DataFrame(
        {
            "bar": pd.DatetimeIndex(pd.to_datetime(df.index, utc=True))
            .tz_convert("UTC")
            .astype("datetime64[ns, UTC]")
        }
    )
    right = prem[["event_time", "premium_close"]].copy()
    right["event_time"] = pd.to_datetime(right["event_time"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    mrg = pd.merge_asof(
        left.sort_values("bar"),
        right.sort_values("event_time"),
        left_on="bar",
        right_on="event_time",
        direction="backward",
    )
    p = pd.Series(mrg["premium_close"].to_numpy(), index=df.index, dtype=float).shift(1)
    fz = (fl - fl.rolling(60, min_periods=30).mean()) / fl.rolling(60, min_periods=30).std().replace(
        0, float("nan")
    )
    pz = (p - p.rolling(60, min_periods=30).mean()) / p.rolling(60, min_periods=30).std().replace(
        0, float("nan")
    )
    # disagree: funding high but premium low (or reverse)
    rules = {
        "fund_hi_prem_lo": ((fz > 0.5) & (pz < 0) & (df["above_sma_50"] == 1)).astype(float),
        "fund_lo_prem_hi": ((fz < -0.5) & (pz > 0) & (df["above_sma_50"] == 1)).astype(float),
        "aligned_bull": ((fz > 0) & (pz > 0) & (df["above_sma_200"] == 1)).astype(float),
        "aligned_calm": ((fz < 0) & (pz < 0) & (df["above_sma_50"] == 1)).astype(float),
    }
    eval_long_flat_rules("ms_prem_fund_disagree_v1", df, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
