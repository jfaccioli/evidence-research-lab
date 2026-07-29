"""Binance public spot klines (no API key required)."""

from __future__ import annotations

import time
from typing import Any

import httpx
import pandas as pd

INTERVAL_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


class BinancePublicSource:
    name = "binance_public"

    def __init__(
        self,
        base_url: str = "https://api.binance.com",
        timeout: float = 30.0,
        sleep_s: float = 0.15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.sleep_s = sleep_s

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        if interval not in INTERVAL_MS:
            raise ValueError(f"Unsupported interval: {interval}")

        rows: list[list[Any]] = []
        cursor = start_ms
        # Default: ~10 years of history if no start
        if cursor is None:
            cursor = int(time.time() * 1000) - 10 * 365 * 24 * 3600 * 1000

        with httpx.Client(timeout=self.timeout) as client:
            while True:
                params: dict[str, Any] = {
                    "symbol": symbol,
                    "interval": interval,
                    "limit": min(limit, 1000),
                    "startTime": cursor,
                }
                if end_ms is not None:
                    params["endTime"] = end_ms

                r = client.get(f"{self.base_url}/api/v3/klines", params=params)
                r.raise_for_status()
                batch = r.json()
                if not batch:
                    break
                rows.extend(batch)
                last_open = batch[-1][0]
                next_cursor = last_open + INTERVAL_MS[interval]
                if end_ms is not None and next_cursor >= end_ms:
                    break
                if len(batch) < min(limit, 1000):
                    break
                # Avoid infinite loop on same candle
                if next_cursor <= cursor:
                    break
                cursor = next_cursor
                time.sleep(self.sleep_s)

        if not rows:
            return _empty_ohlcv()

        df = pd.DataFrame(
            rows,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "n_trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )
        df = df.drop_duplicates(subset=["open_time"]).sort_values("open_time")
        for col in (
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "n_trades",
            "taker_buy_base",
            "taker_buy_quote",
        ):
            df[col] = df[col].astype(float)
        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        # Core OHLCV + kline microstructure observations (previously discarded).
        # taker_buy_* / n_trades are measurable market properties, not close transforms.
        out = df[
            [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "quote_volume",
                "n_trades",
                "taker_buy_base",
                "taker_buy_quote",
            ]
        ].copy()
        # Drop incomplete last candle if still open (close_time in future)
        now_ms = int(time.time() * 1000)
        last_close_time = int(df["close_time"].iloc[-1])
        if last_close_time > now_ms:
            out = out.iloc[:-1]
        return out


def _empty_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "n_trades",
            "taker_buy_base",
            "taker_buy_quote",
        ]
    ).astype(float)
