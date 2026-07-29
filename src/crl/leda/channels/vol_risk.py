"""LEDA-1: Vol / risk evidence channel (Risk layer sink).

Scientific claim (locked):
  Lagged realized volatility is a persistence forecast of next-bar realized
  volatility. High forecast vol → high risk-off evidence score in [0, 1].

Does **not** emit trade signals. Portfolio layer may later map scores to veto.

Design: docs/PROGRAMME_LEDA1_VOL_RISK_V1.md
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.leda.types import EvidenceSink
from crl.leda.util import payload_hash, roll_percentile_rank

CHANNEL_ID = "leda1_vol_risk"
CHANNEL_VERSION = 1
SINK = EvidenceSink.RISK


def _rv(close: pd.Series, window: int) -> pd.Series:
    lr = np.log(close / close.shift(1))
    return lr.rolling(window, min_periods=window).std()


def build_vol_risk_evidence(
    ohlcv: pd.DataFrame,
    *,
    rv_window: int = 20,
    rank_window: int = 60,
    price_col: str = "close",
) -> pd.DataFrame:
    """Build Risk-layer evidence series.

    PIT: score at bar t uses RV computed from returns strictly through t-1
    (``rv_lag = RV_t-1``). ``rv_next`` is evaluation-only (not used in score).
    """
    if price_col not in ohlcv.columns:
        raise ValueError(f"missing {price_col}")
    if rv_window < 2 or rank_window < 5:
        raise ValueError("windows too small")

    close = ohlcv[price_col].astype(float)
    rv_end = _rv(close, rv_window)
    rv_lag = rv_end.shift(1)
    rv_next = rv_end.shift(-1)

    score = roll_percentile_rank(rv_lag, rank_window)

    hashes: list[str] = []
    for ts, rvv in zip(ohlcv.index, rv_lag, strict=False):
        payload = {
            "channel": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "rv_window": rv_window,
            "rank_window": rank_window,
            "ts": str(ts),
            "rv_lag": None if pd.isna(rvv) else round(float(rvv), 12),
        }
        hashes.append(payload_hash(payload))

    return pd.DataFrame(
        {
            "asof_time": [str(t) for t in ohlcv.index],
            "score": score.to_numpy(),
            "inputs_hash": hashes,
            "rv_lag": rv_lag.to_numpy(),
            "rv_next": rv_next.to_numpy(),
            "channel_id": CHANNEL_ID,
            "version": CHANNEL_VERSION,
            "sink": SINK.value,
        },
        index=ohlcv.index,
    )


def evaluate_vol_forecast_skill(
    evidence: pd.DataFrame,
    *,
    min_points: int = 100,
) -> dict[str, Any]:
    """Skill of rv_lag as forecast of rv_next. Not a trading promotion gate."""
    df = evidence.dropna(subset=["rv_lag", "rv_next", "score"]).copy()
    n = len(df)
    if n < min_points:
        return {
            "ok": False,
            "n": n,
            "reason": f"need >= {min_points} points with finite rv_lag and rv_next",
        }
    x = df["rv_lag"].to_numpy(dtype=float)
    y = df["rv_next"].to_numpy(dtype=float)
    sc = df["score"].to_numpy(dtype=float)
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman = float(
        np.corrcoef(pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy())[0, 1]
    )
    score_rv_corr = float(np.corrcoef(sc, x)[0, 1])
    return {
        "ok": True,
        "channel_id": CHANNEL_ID,
        "version": CHANNEL_VERSION,
        "sink": SINK.value,
        "n": n,
        "pearson_rv_lag_vs_rv_next": round(pearson, 6),
        "spearman_rv_lag_vs_rv_next": round(spearman, 6),
        "pearson_score_vs_rv_lag": round(score_rv_corr, 6),
        "claim": "lagged RV persists; high score = high risk-off pressure",
        "note": "Skill metrics only — not promotion to APPROVED trading",
    }
