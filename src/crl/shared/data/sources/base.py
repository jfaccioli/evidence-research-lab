"""Data source protocol."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class OHLCVSource(Protocol):
    name: str

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Return OHLCV with UTC DatetimeIndex named 'timestamp'."""
        ...
