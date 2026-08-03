#!/usr/bin/env python3
"""Funding carry only when |Δpremium| recently small (pre-reg residual filter).

Hedged research: earn funding when in carry; residual = lag abs dpremium.
Only enter when trailing residual scale is low vs funding income.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from crl.shared.config import load_config, project_root
from crl.shared.data.store import latest_manifest, load_dataset
from crl.shared.types import CostConfig
from crl.research.backtest.engine import BacktestResult
from crl.research.market_structure.funding_carry import (
    daily_funding_income,
    asof_funding_rate,
    one_way_cost_fraction,
    _carry_trades,
)
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
    min_tr, smin = int(cfg["gates"]["min_trades"]), float(cfg["gates"]["sharpe_min"])
    mdir = root / cfg["data"]["manifest_dir"]
    df, _ = load_dataset(
        latest_manifest(mdir, symbol="BTCUSDT", interval="1d", source="binance_public").dataset_id,
        mdir,
    )
    df = add_features(df).loc["2019-12-25":]
    funding = pd.read_parquet(
        root / "data/processed/funding/binance_funding_BTCUSDT_funding_d1bbe1f63b23.parquet"
    )
    prem = pd.read_parquet(
        root / "data/processed/premium/binance_premium_BTCUSDT_premium_1d_5f3bba74d0f0.parquet"
    )
    fl = asof_funding_rate(df.index, funding)
    income = daily_funding_income(df.index, funding).shift(1).fillna(0.0)
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
    p = pd.Series(mrg["premium_close"].to_numpy(), index=df.index, dtype=float)
    dprem = p.diff().abs().fillna(0.0)
    resid_scale = dprem.rolling(10, min_periods=5).mean().shift(1)
    # expected daily funding ~ 3 * rate
    exp_inc = (fl.abs() * 3.0).shift(1)

    def side(kind):
        s = pd.Series(0.0, index=df.index)
        if kind == "fund_pos_low_resid":
            m = (fl.shift(1) > 0) & (resid_scale < exp_inc * 0.5)
            s = s.mask(m.fillna(False), 1.0)
        elif kind == "fund_pos_resid_p25":
            thr = resid_scale.expanding(60).quantile(0.25)
            m = (fl.shift(1) > 0) & (resid_scale <= thr)
            s = s.mask(m.fillna(False), 1.0)
        elif kind == "always_low_resid":
            thr = resid_scale.expanding(60).quantile(0.25)
            m = resid_scale <= thr
            s = s.mask(m.fillna(False), 1.0)
        elif kind == "fund_z_low_resid":
            mu = fl.rolling(60, min_periods=30).mean()
            sd = fl.rolling(60, min_periods=30).std()
            z = (fl - mu) / sd.replace(0, np.nan)
            thr = resid_scale.expanding(60).quantile(0.5)
            m = (z.shift(1) > 0) & (resid_scale <= thr)
            s = s.mask(m.fillna(False), 1.0)
        return s.fillna(0.0)

    def run(ohlcv, side_s, stress=False):
        pos = side_s.reindex(ohlcv.index).fillna(0).shift(1).fillna(0)
        inc = income.reindex(ohlcv.index).fillna(0)
        res = dprem.reindex(ohlcv.index).fillna(0).shift(1).fillna(0)
        cf = one_way_cost_fraction(costs, stress=stress)
        delta = pos.diff().fillna(pos.iloc[0])
        net = pos * inc - pos * res - delta.abs() * cf
        w = 1.0
        eq = []
        for x in net.astype(float).values:
            w *= 1 + float(x)
            eq.append(w)
        return BacktestResult(
            equity=pd.Series(eq, index=ohlcv.index),
            position=pos,
            trades=_carry_trades(pos, net),
            bar_returns=net,
            signals=side_s,
            initial_equity=1.0,
        )

    n = len(df)
    i1, i2 = int(n * 0.5), int(n * 0.75)
    va, te = df.iloc[i1:i2], df.iloc[i2:]
    results = []
    for kind in (
        "fund_pos_low_resid",
        "fund_pos_resid_p25",
        "always_low_resid",
        "fund_z_low_resid",
    ):
        s = side(kind)
        r, rs = run(va, s), run(va, s, stress=True)
        met, sm = compute_metrics(r, timeframe="1d"), compute_metrics(rs, timeframe="1d")
        ci = boot(r.bar_returns)
        ok = (
            met.n_trades >= min_tr
            and met.sharpe_after_cost >= smin
            and (np.isnan(ci) or ci >= 0)
            and sm.sharpe_after_cost >= 0
        )
        conf = None
        if ok:
            rt = run(te, s)
            mt = compute_metrics(rt, timeframe="1d")
            ci2 = boot(rt.bar_returns)
            cok = (
                mt.n_trades >= min_tr
                and mt.sharpe_after_cost >= smin
                and (np.isnan(ci2) or ci2 >= 0)
            )
            conf = {
                "status": "candidate" if cok else "failed_test",
                "test_sharpe": mt.sharpe_after_cost,
                "test_trades": mt.n_trades,
            }
        results.append(
            {
                "id": kind,
                "status": "passed_val" if ok else "failed_val",
                "val_sharpe": met.sharpe_after_cost,
                "val_trades": met.n_trades,
                "ci_lo": ci,
                "conf": conf,
            }
        )
        print(kind, results[-1]["status"], conf)
    survivors = [r for r in results if (r.get("conf") or {}).get("status") == "candidate"]
    out = {
        "programme": "ms_carry_low_residual_v1",
        "results": results,
        "survivors": survivors,
        "decision": "SURVIVOR" if survivors else "REJECT",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "live": False,
        "note": "Enter carry only when recent |Δpremium| is low vs funding",
    }
    path = root / "research_kb/rd/MS_CARRY_LOW_RESIDUAL_V1_REPORT.json"
    path.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print("DECISION", out["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
