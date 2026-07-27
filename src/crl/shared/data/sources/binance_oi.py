"""Binance USDT-M open interest history helpers (research; not trading).

Scaffold provides offline parse + versioned save. Live network fetch is
optional and not authorized by the OI programme design step alone.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from crl.shared.data.oi import (
    OIPITError,
    oi_events_content_hash,
    validate_oi_events,
)


DEFAULT_FAPI = "https://fapi.binance.com"


class BinanceOISource:
    """Fetch BTCUSDT (etc.) open-interest history when explicitly invoked."""

    name = "binance_oi"

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

    def _get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        q = urllib.parse.urlencode(params)
        url = f"{self.base_url}{path}?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "crl-research/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise OIPITError(f"binance oi fetch failed: {exc}") from exc
        data = json.loads(raw)
        if not isinstance(data, list):
            raise OIPITError(f"unexpected oi payload type: {type(data)}")
        return data

    def fetch_oi_events(
        self,
        symbol: str = "BTCUSDT",
        *,
        period: str = "1d",
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        limit: int = 500,
        max_pages: int = 50,
    ) -> pd.DataFrame:
        """Paginate /futures/data/openInterestHist into a validated table.

        Caller must version/hash results. Not for confirmatory without programme OK.
        """
        symbol = str(symbol).strip().upper()
        rows: list[dict[str, Any]] = []
        cursor = start_ms
        for _ in range(max_pages):
            params: dict[str, Any] = {
                "symbol": symbol,
                "period": period,
                "limit": min(500, int(limit)),
            }
            if cursor is not None:
                params["startTime"] = int(cursor)
            if end_ms is not None:
                params["endTime"] = int(end_ms)
            page = self._get("/futures/data/openInterestHist", params)
            if not page:
                break
            rows.extend(page)
            last_t = int(page[-1]["timestamp"])
            next_cursor = last_t + 1
            if end_ms is not None and last_t >= end_ms:
                break
            if len(page) < params["limit"]:
                break
            if cursor is not None and next_cursor <= cursor:
                break
            cursor = next_cursor
            time.sleep(self.pause_s)
        if not rows:
            raise OIPITError("no oi rows returned")
        df = pd.DataFrame(
            {
                "oi_time": pd.to_datetime(
                    [int(r["timestamp"]) for r in rows], unit="ms", utc=True
                ),
                "open_interest": [float(r["sumOpenInterest"]) for r in rows],
            }
        )
        df = df.drop_duplicates(subset=["oi_time"], keep="last")
        return validate_oi_events(df)


def events_from_binance_oi_json_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Parse offline fixture rows from Binance openInterestHist JSON."""
    if not records:
        raise OIPITError("empty oi records")
    df = pd.DataFrame(
        {
            "oi_time": pd.to_datetime(
                [int(r["timestamp"]) for r in records], unit="ms", utc=True
            ),
            "open_interest": [float(r["sumOpenInterest"]) for r in records],
        }
    )
    return validate_oi_events(df)


def save_oi_events(
    events: pd.DataFrame,
    *,
    processed_dir: Path,
    source: str,
    symbol: str,
) -> tuple[Path, str, str]:
    """Write versioned OI parquet; return (path, series_id, sha256)."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    sha = oi_events_content_hash(events)
    series_id = f"{source}_{symbol}_oi_{sha[:12]}"
    path = processed_dir / f"{series_id}.parquet"
    if not path.exists():
        events.to_parquet(path, index=False)
    meta = {
        "series_id": series_id,
        "source": source,
        "symbol": symbol,
        "sha256": sha,
        "row_count": len(events),
        "start": str(events["oi_time"].iloc[0]),
        "end": str(events["oi_time"].iloc[-1]),
        "path": str(path),
    }
    (processed_dir / f"{series_id}.json").write_text(json.dumps(meta, indent=2))
    return path, series_id, sha
