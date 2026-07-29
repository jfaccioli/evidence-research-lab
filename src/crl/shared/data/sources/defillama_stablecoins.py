"""Aggregate stablecoin circulating supply from DefiLlama (public free API).

Property: crypto **liquidity stock** (total pegged USD circulating), not exchange
netflow and not a close transform.

PIT policy (binding)
--------------------
DefiLlama daily points are calendar-day aggregates without a revision journal.
We apply a conservative fixed publish lag:

  observation day D (UTC) → event_time = (D + publish_lag_days) 23:59:59 UTC

Default ``publish_lag_days=1``: day-D supply is usable only after the next UTC
day completes (no same-day look-ahead). This is free-research grade, not
vendor-grade PIT.

Attribution: data from DefiLlama stablecoins API (https://defillama.com).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd

DEFAULT_URL = "https://stablecoins.llama.fi/stablecoincharts/all"


class StablecoinSupplyError(ValueError):
    pass


class DefiLlamaStablecoinSource:
    name = "defillama_stablecoins"

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
        if self.publish_lag_days < 0:
            raise StablecoinSupplyError("publish_lag_days must be >= 0")

    def fetch_raw(self) -> list[dict[str, Any]]:
        req = urllib.request.Request(
            self.url, headers={"User-Agent": "crl-research/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise StablecoinSupplyError(f"fetch failed: {exc}") from exc
        if not isinstance(data, list) or not data:
            raise StablecoinSupplyError("empty or unexpected payload")
        return data

    def fetch_supply_events(self) -> pd.DataFrame:
        """Return event_time, supply_usd (total circulating USD peggedUSD)."""
        raw = self.fetch_raw()
        rows: list[dict[str, Any]] = []
        lag = timedelta(days=self.publish_lag_days)
        for pt in raw:
            try:
                ts = int(pt["date"])
            except (KeyError, TypeError, ValueError):
                continue
            circ = pt.get("totalCirculatingUSD") or pt.get("totalCirculating") or {}
            if not isinstance(circ, dict):
                continue
            val = circ.get("peggedUSD")
            if val is None:
                continue
            try:
                supply = float(val)
            except (TypeError, ValueError):
                continue
            if supply <= 0:
                continue
            # calendar day of observation
            day = datetime.fromtimestamp(ts, tz=timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            # available after lag
            event_time = day + lag + timedelta(hours=23, minutes=59, seconds=59)
            rows.append(
                {
                    "event_time": event_time,
                    "obs_day": day,
                    "supply_usd": supply,
                }
            )
        if not rows:
            raise StablecoinSupplyError("no valid supply points")
        df = pd.DataFrame(rows).drop_duplicates(subset=["event_time"]).sort_values(
            "event_time"
        )
        return df.reset_index(drop=True)
