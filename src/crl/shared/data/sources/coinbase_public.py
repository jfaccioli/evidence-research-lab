"""Coinbase Exchange public daily candles (no key; research only).

Used for cross-venue basis vs Binance. Product BTC-USD (USD, not USDT).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd

DEFAULT_BASE = "https://api.exchange.coinbase.com"


class CoinbasePublicError(ValueError):
    pass


class CoinbasePublicSource:
    name = "coinbase_public"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE,
        timeout_s: float = 45.0,
        pause_s: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.pause_s = pause_s

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        q = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "crl-research/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise CoinbasePublicError(f"coinbase fetch failed: {exc}") from exc

    def fetch_daily_closes(
        self,
        product_id: str = "BTC-USD",
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        max_pages: int = 80,
    ) -> pd.DataFrame:
        """Paginate daily candles → trade_date (UTC midnight), close.

        Coinbase candle ``time`` is bucket **open** (unix s). We label by that
        UTC calendar day so it matches Binance daily open-time indexing.
        """
        if end is None:
            end = datetime.now(timezone.utc)
        if start is None:
            start = end - timedelta(days=365 * 8)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        rows: list[list[Any]] = []
        cursor_end = end
        path = f"/products/{product_id}/candles"
        for _ in range(max_pages):
            window_start = max(start, cursor_end - timedelta(days=300))
            params = {
                "granularity": 86400,
                "start": window_start.isoformat().replace("+00:00", "Z"),
                "end": cursor_end.isoformat().replace("+00:00", "Z"),
            }
            batch = self._get(path, params)
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(batch)
            oldest = min(int(r[0]) for r in batch)
            next_end = datetime.fromtimestamp(oldest, tz=timezone.utc) - timedelta(
                seconds=1
            )
            if next_end <= start or next_end >= cursor_end:
                break
            cursor_end = next_end
            time.sleep(self.pause_s)

        if not rows:
            raise CoinbasePublicError("no coinbase candles")

        df = pd.DataFrame(
            rows, columns=["time", "low", "high", "open", "close", "volume"]
        )
        df = df.drop_duplicates(subset=["time"]).sort_values("time")
        # trade_date = UTC midnight of candle open (same convention as Binance 1d index)
        open_ts = pd.to_datetime(df["time"].astype(int), unit="s", utc=True)
        df["trade_date"] = open_ts.dt.floor("D")
        df["close"] = df["close"].astype(float)
        out = (
            df.groupby("trade_date", as_index=False)["close"]
            .last()
            .rename(columns={"close": "cb_close", "trade_date": "event_time"})
        )
        # Drop incomplete last calendar day (still open)
        today = pd.Timestamp.now(tz="UTC").floor("D")
        out = out.loc[out["event_time"] < today].reset_index(drop=True)
        if out.empty:
            raise CoinbasePublicError("all candles incomplete")
        return out
