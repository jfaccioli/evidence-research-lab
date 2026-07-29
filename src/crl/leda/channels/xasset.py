"""LEDA-5a: Cross-asset (ETH→BTC) forecast evidence channel.

Scientific claim (locked):
  Lagged ETH log-momentum is weakly informative about BTC next-bar log return
  (cross-asset underreaction / risk-on co-movement). Map lagged ETH mom to a
  causal rolling percentile rank as long-support score for BTC.

PIT: ETH momentum ending at t-1 only; no same-bar BTC look-ahead in score.
Skill target is BTC forward log return. Not promotion.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.leda.types import EvidenceSink
from crl.leda.util import payload_hash, roll_percentile_rank

CHANNEL_ID = "leda5_xasset"
CHANNEL_VERSION = 1
SINK = EvidenceSink.FORECAST


def build_xasset_evidence(
    btc: pd.DataFrame,
    eth: pd.DataFrame,
    *,
    mom_lookback: int = 20,
    rank_window: int = 60,
    price_col: str = "close",
) -> pd.DataFrame:
    """Build Forecast evidence on BTC index using lagged ETH momentum."""
    if price_col not in btc.columns or price_col not in eth.columns:
        raise ValueError(f"missing {price_col}")
    if mom_lookback < 2 or rank_window < 5:
        raise ValueError("windows too small")

    btc_close = btc[price_col].astype(float)
    eth_close = eth[price_col].astype(float).reindex(btc.index)

    eth_mom_end = np.log(eth_close / eth_close.shift(mom_lookback))
    eth_mom_lag = eth_mom_end.shift(1)
    btc_fwd = np.log(btc_close.shift(-1) / btc_close)

    score = roll_percentile_rank(eth_mom_lag, rank_window)

    hashes: list[str] = []
    for ts, mv in zip(btc.index, eth_mom_lag, strict=False):
        payload = {
            "channel": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "mom_lookback": mom_lookback,
            "rank_window": rank_window,
            "ts": str(ts),
            "eth_mom_lag": None if pd.isna(mv) else round(float(mv), 12),
        }
        hashes.append(payload_hash(payload))

    return pd.DataFrame(
        {
            "asof_time": [str(t) for t in btc.index],
            "score": score.to_numpy(),
            "inputs_hash": hashes,
            "eth_mom_lag": eth_mom_lag.to_numpy(),
            "fwd_ret": btc_fwd.to_numpy(),
            "channel_id": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "sink": SINK.value,
        },
        index=btc.index,
    )


def evaluate_xasset_forecast_skill(
    evidence: pd.DataFrame,
    *,
    min_points: int = 100,
) -> dict[str, Any]:
    """Skill of ETH lagged mom score vs BTC next return. Not promotion."""
    df = evidence.dropna(subset=["eth_mom_lag", "fwd_ret", "score"]).copy()
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "n": n,
            "reason": f"need >= {min_points} points",
        }
    x = df["eth_mom_lag"].to_numpy(dtype=float)
    y = df["fwd_ret"].to_numpy(dtype=float)
    sc = df["score"].to_numpy(dtype=float)

    def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
        if np.std(a) < 1e-15 or np.std(b) < 1e-15:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    pearson_mom = _safe_corr(x, y)
    spearman_score = _safe_corr(
        pd.Series(sc).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    )
    high = sc >= 0.5
    mean_high = float(np.mean(y[high])) if high.any() else float("nan")
    mean_low = float(np.mean(y[~high])) if (~high).any() else float("nan")

    def _r(v: float) -> float | None:
        return round(v, 6) if v == v else None

    return {
        "ok": True,
        "channel_id": CHANNEL_ID,
        "version": CHANNEL_VERSION,
        "sink": SINK.value,
        "n": n,
        "pearson_eth_mom_lag_vs_btc_fwd": _r(pearson_mom),
        "spearman_score_vs_btc_fwd": _r(spearman_score),
        "mean_btc_fwd_score_ge_0_5": round(mean_high, 8) if mean_high == mean_high else None,
        "mean_btc_fwd_score_lt_0_5": round(mean_low, 8) if mean_low == mean_low else None,
        "claim": "lagged ETH mom rank as BTC long-support score; skill only",
        "note": "Skill metrics only — not promotion to APPROVED trading",
    }
