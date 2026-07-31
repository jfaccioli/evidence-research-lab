#!/usr/bin/env python3
"""Run PROGRAMME_MS_FUNDING_CARRY_V1 (research only; temp results)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from crl.research.market_structure.funding_carry import CarryRule, run_funding_carry_backtest
from crl.research.stats.metrics import compute_metrics
from crl.shared.config import load_config, project_root
from crl.shared.data.store import latest_manifest, load_dataset
from crl.shared.types import CostConfig


def chronological_split(df: pd.DataFrame, train=0.5, val=0.25):
    n = len(df)
    i1 = int(n * train)
    i2 = int(n * (train + val))
    return df.iloc[:i1], df.iloc[i1:i2], df.iloc[i2:]


def bootstrap_sharpe_ci_lo(bar_ret: pd.Series, n=400, seed=42) -> float:
    r = bar_ret.dropna().to_numpy(dtype=float)
    if len(r) < 30:
        return float("nan")
    rng = np.random.default_rng(seed)
    sh = []
    for _ in range(n):
        s = rng.choice(r, size=len(r), replace=True)
        sd = s.std(ddof=1)
        if sd < 1e-12:
            sh.append(0.0)
        else:
            sh.append(float(s.mean() / sd * np.sqrt(365)))
    return float(np.percentile(sh, 5))


def main() -> int:
    root = project_root()
    cfg = load_config()
    costs = CostConfig(
        fee_bps_per_side=float(cfg["costs"]["fee_bps_per_side"]),
        half_spread_bps=float(cfg["costs"]["half_spread_bps"]),
        slippage_bps_per_side=float(cfg["costs"]["slippage_bps_per_side"]),
        stress_multiplier=float(cfg["costs"].get("stress_multiplier", 2.0)),
    )
    mdir = root / cfg["data"]["manifest_dir"]
    m = latest_manifest(mdir, symbol="BTCUSDT", interval="1d", source="binance_public")
    ohlcv, _ = load_dataset(m.dataset_id, mdir)
    fund_path = root / "data/processed/funding/binance_funding_BTCUSDT_funding_d1bbe1f63b23.parquet"
    funding = pd.read_parquet(fund_path)

    rules = [
        CarryRule("carry_always", "Always in carry (benchmark premium harvest)", "always_carry"),
        CarryRule("carry_fund_pos", "Carry when last funding rate > 0", "funding_last_pos", 0.0),
        CarryRule("carry_fund_high", "Carry when funding > expanding median", "funding_last_high"),
        CarryRule("carry_z_pos", "Carry when funding z60 > 0", "funding_z_pos", 0.0),
    ]

    min_trades = int(cfg["gates"]["min_trades"])
    sharpe_min = float(cfg["gates"]["sharpe_min"])
    results = []
    for rule in rules:
        res = run_funding_carry_backtest(ohlcv, funding, rule, costs, residual_beta=0.05)
        tr, va, te = chronological_split(ohlcv)
        # re-run on val window only for gate-like check
        res_va = run_funding_carry_backtest(va, funding, rule, costs, residual_beta=0.05)
        met = compute_metrics(res_va, timeframe="1d")
        ci_lo = bootstrap_sharpe_ci_lo(res_va.bar_returns)
        stress = run_funding_carry_backtest(
            va, funding, rule, costs, residual_beta=0.05, stress=True
        )
        sm = compute_metrics(stress, timeframe="1d")
        n_tr = met.n_trades
        sh = float(met.sharpe_after_cost)
        reasons = []
        ok = True
        if n_tr < min_trades:
            ok = False
            reasons.append(f"n_trades {n_tr} < {min_trades}")
        if sh < sharpe_min:
            ok = False
            reasons.append(f"sharpe {sh:.3f} < {sharpe_min}")
        if not np.isnan(ci_lo) and ci_lo < 0:
            ok = False
            reasons.append(f"bootstrap sharpe CI lo {ci_lo:.3f} < 0")
        if float(sm.sharpe_after_cost) < 0:
            ok = False
            reasons.append(f"2x cost stress sharpe {sm.sharpe_after_cost:.3f} < 0")
        # full sample diagnostics
        met_full = compute_metrics(res, timeframe="1d")
        row = {
            "id": rule.id,
            "description": rule.description,
            "status": "passed_val" if ok else "failed_val",
            "val_sharpe": sh,
            "val_trades": n_tr,
            "val_total_return": float(met.total_return),
            "val_max_dd": float(met.max_drawdown),
            "bootstrap_ci_lo": ci_lo,
            "stress_sharpe": float(sm.sharpe_after_cost),
            "full_sharpe": float(met_full.sharpe_after_cost),
            "full_trades": int(met_full.n_trades),
            "reasons": reasons,
        }
        results.append(row)
        print(rule.id, row["status"], f"sh={sh:.3f}", f"n={n_tr}", reasons[:2])

    n_pass = sum(1 for r in results if r["status"] == "passed_val")
    out = {
        "programme": "ms_funding_carry_v1",
        "hypothesis": "H1_market_structure",
        "model": "funding_carry_approx_v1",
        "residual_beta": 0.05,
        "human_auth": "hedged_research_2026-07-31",
        "n_run": len(results),
        "n_passed_val": n_pass,
        "n_failed_val": len(results) - n_pass,
        "results": results,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "decision": "PROMOTE_CANDIDATE_PATH" if n_pass else "REJECT_FAMILY_EXPLORATORY",
        "live": False,
    }
    # confirmatory on test if any pass
    conf = []
    if n_pass:
        for r in results:
            if r["status"] != "passed_val":
                continue
            rule = next(x for x in rules if x.id == r["id"])
            _, _, te = chronological_split(ohlcv)
            res_te = run_funding_carry_backtest(te, funding, rule, costs, residual_beta=0.05)
            mt = compute_metrics(res_te, timeframe="1d")
            ci = bootstrap_sharpe_ci_lo(res_te.bar_returns)
            ok = mt.n_trades >= min_trades and mt.sharpe_after_cost >= sharpe_min and (
                np.isnan(ci) or ci >= 0
            )
            conf.append(
                {
                    "id": rule.id,
                    "status": "candidate" if ok else "failed_test",
                    "test_sharpe": float(mt.sharpe_after_cost),
                    "test_trades": int(mt.n_trades),
                    "bootstrap_ci_lo": ci,
                }
            )
        out["confirmatory"] = conf
        if any(c["status"] == "candidate" for c in conf):
            out["decision"] = "SURVIVOR_RESEARCH_ONLY_NO_LIVE"
        else:
            out["decision"] = "REJECT_AFTER_CONFIRMATORY"

    path = root / "research_kb/rd/MS_FUNDING_CARRY_V1_REPORT.json"
    path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print("decision", out["decision"], "saved", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
