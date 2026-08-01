#!/usr/bin/env python3
"""Long when funding not crowded (z low) and slow trend — distinct pre-reg set."""
from __future__ import annotations
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from crl.shared.config import load_config, project_root
from crl.shared.data.store import latest_manifest, load_dataset
from crl.shared.types import CostConfig
from crl.research.backtest.engine import run_backtest_desired
from crl.research.stats.metrics import compute_metrics
from crl.shared.data.features import add_features
from crl.research.market_structure.funding_carry import asof_funding_rate

def boot(r, n=300):
    x = r.dropna().to_numpy(float)
    if len(x) < 30: return float("nan")
    rng = np.random.default_rng(42)
    sh = []
    for _ in range(n):
        s = rng.choice(x, size=len(x), replace=True)
        sd = s.std(ddof=1)
        sh.append(0.0 if sd < 1e-12 else float(s.mean() / sd * np.sqrt(365)))
    return float(np.percentile(sh, 5))

def main() -> int:
    root = project_root(); cfg = load_config()
    costs = CostConfig(fee_bps_per_side=float(cfg["costs"]["fee_bps_per_side"]), half_spread_bps=float(cfg["costs"]["half_spread_bps"]), slippage_bps_per_side=float(cfg["costs"]["slippage_bps_per_side"]), stress_multiplier=float(cfg["costs"].get("stress_multiplier", 2)))
    min_tr, smin = int(cfg["gates"]["min_trades"]), float(cfg["gates"]["sharpe_min"])
    mdir = root / cfg["data"]["manifest_dir"]
    df, _ = load_dataset(latest_manifest(mdir, symbol="BTCUSDT", interval="1d", source="binance_public").dataset_id, mdir)
    df = add_features(df).loc["2020-01-01":]
    fl = asof_funding_rate(df.index, pd.read_parquet(root / "data/processed/funding/binance_funding_BTCUSDT_funding_d1bbe1f63b23.parquet")).shift(1)
    z = (fl - fl.rolling(60, min_periods=30).mean()) / fl.rolling(60, min_periods=30).std().replace(0, np.nan)
    rules = {
        "z_neg_sma200": ((z < 0) & (df["above_sma_200"] == 1)).astype(float),
        "z_lt1_sma50": ((z < 1) & (df["above_sma_50"] == 1)).astype(float),
        "fund_neg_sma50": ((fl < 0) & (df["above_sma_50"] == 1)).astype(float),
        "z_lt0_sma50": ((z < 0) & (df["above_sma_50"] == 1)).astype(float),
    }
    n = len(df); i1, i2 = int(n * 0.5), int(n * 0.75)
    va, te = df.iloc[i1:i2], df.iloc[i2:]
    results = []
    for rid, des in rules.items():
        des = des.fillna(0).clip(0, 1)
        r = run_backtest_desired(va, des.reindex(va.index).fillna(0), costs)
        rs = run_backtest_desired(va, des.reindex(va.index).fillna(0), costs, stress=True)
        met, sm = compute_metrics(r, timeframe="1d"), compute_metrics(rs, timeframe="1d")
        ci = boot(r.bar_returns)
        ok = met.n_trades >= min_tr and met.sharpe_after_cost >= smin and (np.isnan(ci) or ci >= 0) and sm.sharpe_after_cost >= 0
        conf = None
        if ok:
            rt = run_backtest_desired(te, des.reindex(te.index).fillna(0), costs)
            mt = compute_metrics(rt, timeframe="1d"); ci2 = boot(rt.bar_returns)
            cok = mt.n_trades >= min_tr and mt.sharpe_after_cost >= smin and (np.isnan(ci2) or ci2 >= 0)
            conf = {"status": "candidate" if cok else "failed_test", "test_sharpe": mt.sharpe_after_cost}
        results.append({"id": rid, "status": "passed_val" if ok else "failed_val", "val_sharpe": met.sharpe_after_cost, "val_trades": met.n_trades, "ci_lo": ci, "conf": conf})
        print(rid, results[-1]["status"], conf)
    survivors = [r for r in results if (r.get("conf") or {}).get("status") == "candidate"]
    out = {"programme": "ms_fund_neg_crowding_v1", "results": results, "survivors": survivors, "decision": "SURVIVOR" if survivors else "REJECT", "ran_at": datetime.now(timezone.utc).isoformat(), "live": False}
    (root / "research_kb/rd/MS_FUND_NEG_CROWDING_V1_REPORT.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    print("DECISION", out["decision"]); return 0

if __name__ == "__main__":
    raise SystemExit(main())
