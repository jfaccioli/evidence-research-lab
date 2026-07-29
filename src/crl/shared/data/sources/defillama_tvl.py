"""Aggregate DeFi TVL history from DefiLlama (public free API).

Property: capital locked in DeFi protocols (totalLiquidityUSD) — risk-on
capital allocation distinct from spot OHLCV and stablecoin *circulating* supply.

PIT: same conservative lag policy as stablecoin supply (publish_lag_days=1).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

DEFAULT_URL = "https://api.llama.fi/charts"


class DefiTvlError(ValueError):
    pass


class DefiLlamaTvlSource:
    name = "defillama_tvl"

    def __init__(
        self,
        *,
        url: str = DEFAULT_URL,
        timeout_s: float = 90.0,
        publish_lag_days: int = 1,
    ) -> None:
        self.url = url
        self.timeout_s = timeout_s
        self.publish_lag_days = int(publish_lag_days)

    def fetch_tvl_events(self) -> pd.DataFrame:
        req = urllib.request.Request(
            self.url, headers={"User-Agent": "crl-research/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise DefiTvlError(f"fetch failed: {exc}") from exc
        if not isinstance(data, list) or not data:
            raise DefiTvlError("empty TVL payload")

        lag = timedelta(days=self.publish_lag_days)
        rows: list[dict[str, Any]] = []
        for pt in data:
            try:
                ts = int(pt["date"])
                tvl = float(pt.get("totalLiquidityUSD") or pt.get("tvl") or 0)
            except (KeyError, TypeError, ValueError):
                continue
            if tvl <= 0:
                continue
            day = datetime.fromtimestamp(ts, tz=timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            event_time = day + lag + timedelta(hours=23, minutes=59, seconds=59)
            rows.append({"event_time": event_time, "tvl_usd": tvl})
        if not rows:
            raise DefiTvlError("no positive TVL points")
        df = pd.DataFrame(rows).drop_duplicates(subset=["event_time"]).sort_values(
            "event_time"
        )
        return df.reset_index(drop=True)
