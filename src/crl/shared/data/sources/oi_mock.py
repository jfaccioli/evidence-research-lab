"""Deterministic mock open-interest snapshots for unit tests (not science)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_mock_oi_events(
    *,
    start: str | pd.Timestamp = "2019-01-01",
    end: str | pd.Timestamp = "2024-01-01",
    step_hours: int = 8,
    seed: int = 42,
    base_oi: float = 1.0e9,
) -> pd.DataFrame:
    """Synthetic oi_time / open_interest series (exchange-like sparse grid)."""
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    times = pd.date_range(start_ts, end_ts, freq=f"{step_hours}h", inclusive="left")
    rng = np.random.default_rng(seed)
    n = len(times)
    # Slow random walk in log-OI with mild mean reversion (always positive).
    log_oi = np.log(base_oi)
    levels = np.empty(n, dtype=float)
    for i in range(n):
        log_oi = 0.999 * log_oi + 0.001 * np.log(base_oi) + rng.normal(0, 0.002)
        if rng.random() < 0.02:
            log_oi += rng.choice([-1.0, 1.0]) * rng.uniform(0.01, 0.04)
        levels[i] = float(np.exp(log_oi))
    return pd.DataFrame({"oi_time": times, "open_interest": levels})
