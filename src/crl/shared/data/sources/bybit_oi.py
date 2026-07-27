"""Bybit linear open-interest history (research; not trading).

Binance public ``openInterestHist`` only retains ~30 daily points without
usable deep startTime. Bybit v5 market open-interest provides multi-year
daily history suitable for the OI PIT programme when labeled honestly as
``bybit_oi`` (not Binance).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

import pandas as pd

from crl.shared.data.oi import OIPITError, validate_oi_events


DEFAULT_BYBIT = "https://api.bybit.com"


class BybitOISource:
    """Fetch BTCUSDT linear perpetual open-interest history from Bybit v5."""

    name = "bybit_oi"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BYBIT,
        timeout_s: float = 30.0,
        pause_s: float = 0.15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.pause_s = pause_s

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        q = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "crl-research/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise OIPITError(f"bybit oi fetch failed: {exc}") from exc
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise OIPITError(f"unexpected bybit payload type: {type(data)}")
        if int(data.get("retCode", -1)) != 0:
            raise OIPITError(f"bybit oi error: {data.get('retMsg')}")
        return data

    def fetch_oi_events(
        self,
        symbol: str = "BTCUSDT",
        *,
        category: str = "linear",
        interval_time: str = "1d",
        limit: int = 200,
        max_pages: int = 100,
        end_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Paginate /v5/market/open-interest (newest pages first)."""
        symbol = str(symbol).strip().upper()
        rows: list[dict[str, Any]] = []
        cursor_end = end_ms
        for _ in range(max_pages):
            params: dict[str, Any] = {
                "category": category,
                "symbol": symbol,
                "intervalTime": interval_time,
                "limit": min(200, int(limit)),
            }
            if cursor_end is not None:
                params["endTime"] = int(cursor_end)
            data = self._get("/v5/market/open-interest", params)
            page = (data.get("result") or {}).get("list") or []
            if not page:
                break
            rows.extend(page)
            ts = [int(x["timestamp"]) for x in page]
            oldest = min(ts)
            next_end = oldest - 1
            if cursor_end is not None and next_end >= cursor_end:
                break
            cursor_end = next_end
            if len(page) < 2:
                break
            time.sleep(self.pause_s)
        if not rows:
            raise OIPITError("no bybit oi rows returned")
        by_ts: dict[int, float] = {}
        for r in rows:
            by_ts[int(r["timestamp"])] = float(r["openInterest"])
        times = sorted(by_ts)
        df = pd.DataFrame(
            {
                "oi_time": pd.to_datetime(times, unit="ms", utc=True),
                "open_interest": [by_ts[t] for t in times],
            }
        )
        return validate_oi_events(df)


def events_from_bybit_json_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Parse offline fixture rows shaped like Bybit open-interest list items."""
    if not records:
        raise OIPITError("empty bybit oi records")
    df = pd.DataFrame(
        {
            "oi_time": pd.to_datetime(
                [int(r["timestamp"]) for r in records], unit="ms", utc=True
            ),
            "open_interest": [float(r["openInterest"]) for r in records],
        }
    )
    return validate_oi_events(df)
