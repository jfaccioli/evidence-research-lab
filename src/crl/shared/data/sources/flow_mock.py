"""Deterministic mock exchange-flow series for unit tests (not science)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_mock_flow_events(
    *,
    start: str | pd.Timestamp = "2019-01-01",
    end: str | pd.Timestamp = "2024-01-01",
    step_hours: int = 24,
    seed: int = 42,
) -> pd.DataFrame:
    """Synthetic flow_time / net_flow (BTC units proxy)."""
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    times = pd.date_range(start_ts, end_ts, freq=f"{step_hours}h", inclusive="left")
    rng = np.random.default_rng(seed)
    n = len(times)
    x = 0.0
    flows = np.empty(n, dtype=float)
    for i in range(n):
        x = 0.9 * x + rng.normal(0, 50.0)
        if rng.random() < 0.02:
            x += rng.choice([-1.0, 1.0]) * rng.uniform(200, 800)
        flows[i] = x
    return pd.DataFrame({"flow_time": times, "net_flow": flows})
