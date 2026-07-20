"""Deterministic synthetic OHLCV for unit tests (no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd


class MockOHLCVSource:
    name = "mock"

    def __init__(self, n: int = 1200, seed: int = 0, start: str = "2018-01-01") -> None:
        self.n = n
        self.seed = seed
        self.start = start

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        # Mild drift + noise so SMA strategies have path structure
        rets = rng.normal(0.0003, 0.02, size=self.n)
        close = 10_000 * np.exp(np.cumsum(rets))
        open_ = np.concatenate([[close[0]], close[:-1]])
        high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.005, self.n))
        low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.005, self.n))
        volume = rng.uniform(100, 1000, self.n)
        freq = "1D" if interval in ("1d", "1D") else "4h"
        idx = pd.date_range(self.start, periods=self.n, freq=freq, tz="UTC")
        return pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
            index=idx,
        )
