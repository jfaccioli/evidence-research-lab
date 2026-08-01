#!/usr/bin/env python3
"""Ticket: long when cross-venue basis compressed + trend."""
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

def boot(r, n=300):
    x = r.dropna().to_numpy(float)
    if len(x) < 30:
        return float("nan")
    rng = np.random.default_rng(42)
    sh = []
    for _ in range(n):
        s = rng.choice(x, size=len(x), replace=True)
        sd = s.std(ddof=1)
        sh.append(0.0 if sd < 1e-12 else float(s.mean() / sd * np.sqrt(365)))
    return float(np.percentile(sh, 5))

def main() -> int:
    root = project_root()
    cfg = load_config()
    costs = CostConfig(
        fee_bps_per_side=float(cfg["costs"]["fee_bps_per_side"]),
        half_spread_bps=float(cfg["costs"]["half_spread_bps"]),
        slippage_bps_per_side=float(cfg["costs"]["slippage_bps_per_side"]),
        stress_multiplier=float(cfg["costs"].get("stress_multiplier", 2)),
    )
    min_tr = int(cfg["gates"]["min_trades"])
    smin = float(cfg["gates"]["sharpe_min"])
    mdir = root / cfg["data"]["manifest_dir"]
    m = latest_manifest(mdir, symbol="BTCUSDT", interval="1d", source="binance_public")
    df, _ = load_dataset(m.dataset_id, mdir)
    df = add_features(df).loc["2020-01-01":]
    cv = pd.read_parquet(root / "data/processed/cross_venue/cross_venue_binance_usdt_vs_coinbase_usd_d54a084a5189.parquet")
    bars = pd.DatetimeIndex(pd.to_datetime(df.index, utc=True)).tz_convert("UTC").astype("datetime64[ns, UTC]")
    left = pd.DataFrame({"bar": bars})
    right = cv[["event_time", "basis"]].copy()
    right["event_time"] = pd.to_datetime(right["event_time"], utc=True).astype("datetime64[ns, UTC]")
    mrg = pd.merge_asof(left.sort_values("bar"), right.sort_values("event_time"), left_on="bar", right_on="event_time", direction="backward")
    basis = pd.Series(mrg["basis"].to_numpy(), index=df.index, dtype=float).shift(1)
    z = (basis - basis.rolling(60, min_periods=30).mean()) / basis.rolling(60, min_periods=30).std().replace(0, np.nan)
    med = basis.expanding(60).median()
    rules = {
        "basis_z_neg_trend": ((z < 0) & (df["above_sma_50"] == 1)).astype(float),
        "basis_below_med_trend": ((basis < med) & (df["above_sma_200"] == 1)).astype(float),
        "basis_not_ext_trend": ((z < 1.0) & (df["above_sma_50"] == 1)).astype(float),
        "basis_neg_sma50": ((basis < 0) & (df["above_sma_50"] == 1)).astype(float),
    }
    n = len(df)
    i1, i2 = int(n * 0.5), int(n * 0.75)
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
            mt = compute_metrics(rt, timeframe="1d")
            ci2 = boot(rt.bar_returns)
            cok = mt.n_trades >= min_tr and mt.sharpe_after_cost >= smin and (np.isnan(ci2) or ci2 >= 0)
            conf = {"status": "candidate" if cok else "failed_test", "test_sharpe": mt.sharpe_after_cost}
        results.append({"id": rid, "status": "passed_val" if ok else "failed_val", "val_sharpe": met.sharpe_after_cost, "val_trades": met.n_trades, "ci_lo": ci, "conf": conf})
        print(rid, results[-1]["status"], conf)
    survivors = [r for r in results if (r.get("conf") or {}).get("status") == "candidate"]
    out = {"programme": "ms_basis_long_v1", "results": results, "survivors": survivors, "decision": "SURVIVOR" if survivors else "REJECT", "ran_at": datetime.now(timezone.utc).isoformat(), "live": False}
    (root / "research_kb/rd/MS_BASIS_LONG_V1_REPORT.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    print("DECISION", out["decision"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
