#!/usr/bin/env python3
"""NEW angle: BTC vs ETH relative strength — long BTC when it leads ETH (RS)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.lib_autonomous_gates import eval_long_flat_rules, load_btc_1d, load_eth_1d


def main() -> int:
    btc = load_btc_1d()
    eth = load_eth_1d()
    # align
    idx = btc.index.intersection(eth.index)
    btc, eth = btc.loc[idx], eth.loc[idx]
    br = btc["close"].pct_change(20)
    er = eth["close"].pct_change(20)
    rs = (br - er).shift(1)  # lag RS
    rs_z = (rs - rs.rolling(60, min_periods=30).mean()) / rs.rolling(
        60, min_periods=30
    ).std().replace(0, float("nan"))
    rules = {
        "btc_leads_eth_trend": ((rs > 0) & (btc["above_sma_50"] == 1)).astype(float),
        "btc_rs_z_pos": ((rs_z > 0) & (btc["above_sma_200"] == 1)).astype(float),
        "btc_leads_strong": ((rs_z > 0.5) & (btc["above_sma_50"] == 1)).astype(float),
        # mean-revert RS: long BTC when lagging (catch-up) + mild trend
        "btc_lags_catchup": ((rs_z < -0.5) & (btc["above_sma_200"] == 1)).astype(float),
    }
    eval_long_flat_rules("ms_btc_eth_rs_v1", btc, rules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
