"""LEDA-2: Trend / structure forecast evidence channel (Forecast layer sink).

Scientific claim (locked):
  Lagged multi-bar log-momentum is weakly informative about next-bar log return.
  Mapping lagged momentum to a causal rolling percentile rank yields
  **risk-on / long-support evidence** in [0, 1].

Does **not** emit position sizes or orders. Portfolio may later map scores.

Design: docs/PROGRAMME_LEDA2_TREND_V1.md
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.leda.types import EvidenceSink
from crl.leda.util import payload_hash, roll_percentile_rank

CHANNEL_ID = "leda2_trend"
CHANNEL_VERSION = 1
SINK = EvidenceSink.FORECAST


def build_trend_evidence(
    ohlcv: pd.DataFrame,
    *,
    mom_lookback: int = 20,
    rank_window: int = 60,
    price_col: str = "close",
) -> pd.DataFrame:
    """Build Forecast-layer evidence series.

    PIT: score at bar t uses momentum ending at t-1 only
    (``mom_lag = log(c_{t-1}/c_{t-1-L})``). ``fwd_ret`` is evaluation-only.
    """
    if price_col not in ohlcv.columns:
        raise ValueError(f"missing {price_col}")
    if mom_lookback < 2 or rank_window < 5:
        raise ValueError("windows too small")

    close = ohlcv[price_col].astype(float)
    # Momentum known at end of bar t: log(c_t / c_{t-L})
    mom_end = np.log(close / close.shift(mom_lookback))
    # Strict lag: decision-time score at t uses only data through t-1
    mom_lag = mom_end.shift(1)
    # Next-bar log return from t → t+1 (skill target only)
    fwd_ret = np.log(close.shift(-1) / close)

    score = roll_percentile_rank(mom_lag, rank_window)

    hashes: list[str] = []
    for ts, mv in zip(ohlcv.index, mom_lag, strict=False):
        payload = {
            "channel": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "mom_lookback": mom_lookback,
            "rank_window": rank_window,
            "ts": str(ts),
            "mom_lag": None if pd.isna(mv) else round(float(mv), 12),
        }
        hashes.append(payload_hash(payload))

    return pd.DataFrame(
        {
            "asof_time": [str(t) for t in ohlcv.index],
            "score": score.to_numpy(),
            "inputs_hash": hashes,
            "mom_lag": mom_lag.to_numpy(),
            "fwd_ret": fwd_ret.to_numpy(),
            "channel_id": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "sink": SINK.value,
        },
        index=ohlcv.index,
    )


def evaluate_trend_forecast_skill(
    evidence: pd.DataFrame,
    *,
    min_points: int = 100,
) -> dict[str, Any]:
    """Skill of score / mom_lag vs next-bar return. Not a trading promotion gate."""
    df = evidence.dropna(subset=["mom_lag", "fwd_ret", "score"]).copy()
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "n": n,
            "reason": f"need >= {min_points} points with finite mom_lag, fwd_ret, score",
        }
    x = df["mom_lag"].to_numpy(dtype=float)
    y = df["fwd_ret"].to_numpy(dtype=float)
    sc = df["score"].to_numpy(dtype=float)

    def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
        if np.std(a) < 1e-15 or np.std(b) < 1e-15:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    pearson_mom = _safe_corr(x, y)
    spearman_mom = _safe_corr(
        pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    )
    pearson_score = _safe_corr(sc, y)
    spearman_score = _safe_corr(
        pd.Series(sc).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    )
    # Directional: high score vs positive next return
    high = sc >= 0.5
    low = sc < 0.5
    mean_ret_high = float(np.mean(y[high])) if high.any() else float("nan")
    mean_ret_low = float(np.mean(y[low])) if low.any() else float("nan")
    hit_high = float(np.mean(y[high] > 0)) if high.any() else float("nan")

    return {
        "ok": True,
        "channel_id": CHANNEL_ID,
        "version": CHANNEL_VERSION,
        "sink": SINK.value,
        "n": n,
        "pearson_mom_lag_vs_fwd_ret": round(pearson_mom, 6) if pearson_mom == pearson_mom else None,
        "spearman_mom_lag_vs_fwd_ret": round(spearman_mom, 6) if spearman_mom == spearman_mom else None,
        "pearson_score_vs_fwd_ret": round(pearson_score, 6) if pearson_score == pearson_score else None,
        "spearman_score_vs_fwd_ret": round(spearman_score, 6) if spearman_score == spearman_score else None,
        "mean_fwd_ret_score_ge_0_5": round(mean_ret_high, 8) if mean_ret_high == mean_ret_high else None,
        "mean_fwd_ret_score_lt_0_5": round(mean_ret_low, 8) if mean_ret_low == mean_ret_low else None,
        "hit_rate_fwd_pos_when_score_ge_0_5": round(hit_high, 6) if hit_high == hit_high else None,
        "claim": "lagged mom rank = long-support score; skill only",
        "note": "Skill metrics only — not promotion to APPROVED trading",
    }
