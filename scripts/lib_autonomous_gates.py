"""Shared helpers for autonomous research tickets (frozen-style gates)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from crl.research.backtest.engine import run_backtest_desired
from crl.research.stats.metrics import compute_metrics
from crl.shared.config import load_config, project_root
from crl.shared.data.features import add_features
from crl.shared.data.store import latest_manifest, load_dataset
from crl.shared.types import CostConfig


def load_btc_1d(start: str = "2020-01-01") -> pd.DataFrame:
    root = project_root()
    cfg = load_config()
    mdir = root / cfg["data"]["manifest_dir"]
    m = latest_manifest(mdir, symbol="BTCUSDT", interval="1d", source="binance_public")
    df, _ = load_dataset(m.dataset_id, mdir)
    return add_features(df).loc[start:]


def load_eth_1d(start: str = "2020-01-01") -> pd.DataFrame:
    root = project_root()
    cfg = load_config()
    mdir = root / cfg["data"]["manifest_dir"]
    m = latest_manifest(mdir, symbol="ETHUSDT", interval="1d", source="binance_public")
    df, _ = load_dataset(m.dataset_id, mdir)
    return add_features(df).loc[start:]


def costs_from_cfg() -> CostConfig:
    cfg = load_config()
    return CostConfig(
        fee_bps_per_side=float(cfg["costs"]["fee_bps_per_side"]),
        half_spread_bps=float(cfg["costs"]["half_spread_bps"]),
        slippage_bps_per_side=float(cfg["costs"]["slippage_bps_per_side"]),
        stress_multiplier=float(cfg["costs"].get("stress_multiplier", 2)),
    )


def gate_params() -> tuple[int, float]:
    cfg = load_config()
    return int(cfg["gates"]["min_trades"]), float(cfg["gates"]["sharpe_min"])


def boot_lo(bar_ret: pd.Series, ann: float = 365.0, n: int = 300, seed: int = 42) -> float:
    x = bar_ret.dropna().to_numpy(dtype=float)
    if len(x) < 30:
        return float("nan")
    rng = np.random.default_rng(seed)
    sh = []
    for _ in range(n):
        s = rng.choice(x, size=len(x), replace=True)
        sd = s.std(ddof=1)
        sh.append(0.0 if sd < 1e-12 else float(s.mean() / sd * np.sqrt(ann)))
    return float(np.percentile(sh, 5))


def eval_long_flat_rules(
    programme: str,
    ohlcv: pd.DataFrame,
    rules: dict[str, pd.Series],
    *,
    ann: float = 365.0,
) -> dict[str, Any]:
    costs = costs_from_cfg()
    min_tr, smin = gate_params()
    n = len(ohlcv)
    i1, i2 = int(n * 0.5), int(n * 0.75)
    va, te = ohlcv.iloc[i1:i2], ohlcv.iloc[i2:]
    results = []
    for rid, des in rules.items():
        des = des.reindex(ohlcv.index).fillna(0).clip(0, 1).astype(float)
        r = run_backtest_desired(va, des.reindex(va.index).fillna(0), costs)
        rs = run_backtest_desired(va, des.reindex(va.index).fillna(0), costs, stress=True)
        met = compute_metrics(r, timeframe="1d")
        sm = compute_metrics(rs, timeframe="1d")
        ci = boot_lo(r.bar_returns, ann=ann)
        ok = (
            met.n_trades >= min_tr
            and met.sharpe_after_cost >= smin
            and (np.isnan(ci) or ci >= 0)
            and sm.sharpe_after_cost >= 0
        )
        conf = None
        if ok:
            rt = run_backtest_desired(te, des.reindex(te.index).fillna(0), costs)
            mt = compute_metrics(rt, timeframe="1d")
            ci2 = boot_lo(rt.bar_returns, ann=ann)
            cok = (
                mt.n_trades >= min_tr
                and mt.sharpe_after_cost >= smin
                and (np.isnan(ci2) or ci2 >= 0)
            )
            conf = {
                "status": "candidate" if cok else "failed_test",
                "test_sharpe": mt.sharpe_after_cost,
                "test_trades": mt.n_trades,
                "ci_lo": ci2,
            }
        results.append(
            {
                "id": rid,
                "status": "passed_val" if ok else "failed_val",
                "val_sharpe": met.sharpe_after_cost,
                "val_trades": met.n_trades,
                "ci_lo": ci,
                "stress": sm.sharpe_after_cost,
                "conf": conf,
            }
        )
        print(rid, results[-1]["status"], conf)
    survivors = [r for r in results if (r.get("conf") or {}).get("status") == "candidate"]
    out = {
        "programme": programme,
        "results": results,
        "survivors": survivors,
        "decision": "SURVIVOR" if survivors else "REJECT",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "live": False,
    }
    path = project_root() / "research_kb" / "rd" / f"{programme.upper()}_REPORT.json"
    path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print("DECISION", out["decision"], "->", path.name)
    return out
