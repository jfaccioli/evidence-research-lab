"""Binance USDT-M perpetual premium index klines (public; research only).

Premium index ≈ (mark − index) / index over the bar — a futures-consensus
deviation from spot/index, related to but not identical to discrete funding.

Endpoint: GET /fapi/v1/premiumIndexKlines
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

import pandas as pd

DEFAULT_FAPI = "https://fapi.binance.com"

INTERVAL_MS = {
    "1d": 86_400_000,
    "4h": 14_400_000,
    "1h": 3_600_000,
}


class PremiumPITError(ValueError):
    pass


class BinancePremiumSource:
    """Fetch perpetual premium index kline history."""

    name = "binance_premium"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_FAPI,
        timeout_s: float = 30.0,
        pause_s: float = 0.15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.pause_s = pause_s

    def _get(self, path: str, params: dict[str, Any]) -> list[Any]:
        q = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "crl-research/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise PremiumPITError(f"premium fetch failed: {exc}") from exc
        data = json.loads(raw)
        if not isinstance(data, list):
            raise PremiumPITError(f"unexpected payload type: {type(data)}")
        return data

    def fetch_premium_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        *,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        limit: int = 1500,
        max_pages: int = 40,
    ) -> pd.DataFrame:
        """Paginate premiumIndexKlines → open/high/low/close premium series."""
        if interval not in INTERVAL_MS:
            raise PremiumPITError(f"unsupported interval {interval}")
        symbol = str(symbol).strip().upper()
        rows: list[list[Any]] = []
        cursor = start_ms
        if cursor is None:
            # ~8y of daily history is enough for characterization
            cursor = int(time.time() * 1000) - 8 * 365 * 24 * 3600 * 1000

        for _ in range(max_pages):
            params: dict[str, Any] = {
                "symbol": symbol,
                "interval": interval,
                "limit": min(1500, int(limit)),
                "startTime": int(cursor),
            }
            if end_ms is not None:
                params["endTime"] = int(end_ms)
            page = self._get("/fapi/v1/premiumIndexKlines", params)
            if not page:
                break
            rows.extend(page)
            last_open = int(page[-1][0])
            next_cursor = last_open + INTERVAL_MS[interval]
            if end_ms is not None and next_cursor >= end_ms:
                break
            if len(page) < params["limit"]:
                break
            if next_cursor <= cursor:
                break
            cursor = next_cursor
            time.sleep(self.pause_s)

        if not rows:
            raise PremiumPITError("no premium kline rows returned")

        df = pd.DataFrame(
            rows,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "ignore_vol",
                "close_time",
                "ignore_q",
                "n_trades",
                "ignore_tb",
                "ignore_tq",
                "ignore",
            ],
        )
        df = df.drop_duplicates(subset=["open_time"]).sort_values("open_time")
        for col in ("open", "high", "low", "close"):
            df[col] = df[col].astype(float)
        # event_time = bar close (premium for the completed bar is known at close)
        df["event_time"] = pd.to_datetime(df["close_time"].astype(int), unit="ms", utc=True)
        out = pd.DataFrame(
            {
                "event_time": df["event_time"],
                "premium_open": df["open"].to_numpy(),
                "premium_high": df["high"].to_numpy(),
                "premium_low": df["low"].to_numpy(),
                "premium_close": df["close"].to_numpy(),
            }
        ).reset_index(drop=True)
        # Drop incomplete last bar if close_time in future
        now = pd.Timestamp.now(tz="UTC")
        out = out.loc[out["event_time"] <= now].reset_index(drop=True)
        if out.empty:
            raise PremiumPITError("all premium bars incomplete")
        return out
