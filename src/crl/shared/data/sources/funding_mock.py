"""Deterministic mock perpetual funding events for unit tests (not science)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_mock_funding_events(
    *,
    start: str | pd.Timestamp = "2019-01-01",
    end: str | pd.Timestamp = "2024-01-01",
    step_hours: int = 8,
    seed: int = 42,
) -> pd.DataFrame:
    """Synthetic funding_time / funding_rate series (exchange-like 8h grid)."""
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    times = pd.date_range(start_ts, end_ts, freq=f"{step_hours}h", inclusive="left")
    rng = np.random.default_rng(seed)
    # Mild mean-reverting AR(1) around 0 with rare spikes
    n = len(times)
    rates = np.zeros(n, dtype=float)
    x = 0.0
    for i in range(n):
        x = 0.85 * x + rng.normal(0, 0.00005)
        if rng.random() < 0.01:
            x += rng.choice([-1.0, 1.0]) * rng.uniform(0.0003, 0.001)
        rates[i] = x
    return pd.DataFrame({"funding_time": times, "funding_rate": rates})
