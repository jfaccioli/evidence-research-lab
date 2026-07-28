"""Polymarket CLOB public prices-history → external daily series (no API key).

PIT: observation at CLOB candle time t is known at t; we apply an extra
``publish_lag_days`` (default 1) so same-calendar-day BTC bars cannot use
same-day odds (conservative).

Selection must be pre-registered in the programme design (token_id locked).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.config import project_root
from crl.shared.data.external_series import (
    external_events_hash,
    validate_external_events,
)

CLOB = "https://clob.polymarket.com"
GAMMA = "https://gamma-api.polymarket.com"


def _http_get(url: str, params: dict[str, Any] | None = None, timeout: float = 90.0) -> Any:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "evidence-research-lab/crl"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_prices_history(
    token_id: str,
    *,
    interval: str = "max",
    fidelity: int = 1440,
) -> list[dict[str, Any]]:
    ph = _http_get(
        f"{CLOB}/prices-history",
        {"market": token_id, "interval": interval, "fidelity": fidelity},
    )
    return list(ph.get("history") or [])


def history_to_events(
    history: list[dict[str, Any]],
    *,
    publish_lag_days: int = 1,
) -> pd.DataFrame:
    if not history:
        raise ValueError("empty prices-history")
    rows = []
    for h in history:
        t = datetime.fromtimestamp(int(h["t"]), tz=timezone.utc)
        # daily fidelity → treat as known at that timestamp + lag days
        event_time = t + timedelta(days=int(publish_lag_days))
        rows.append({"event_time": event_time, "value": float(h["p"])})
    df = pd.DataFrame(rows).drop_duplicates(subset=["event_time"], keep="last")
    return validate_external_events(df)


def ingest_token_series(
    token_id: str,
    *,
    series_id: str,
    publish_lag_days: int = 1,
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = project_root()
    out_dir = root / "data" / "processed" / "external"
    out_dir.mkdir(parents=True, exist_ok=True)
    hist = fetch_prices_history(token_id)
    events = history_to_events(hist, publish_lag_days=publish_lag_days)
    path = out_dir / f"{series_id}.parquet"
    events.to_parquet(path, index=False)
    h = external_events_hash(events)
    meta = {
        "series_id": series_id,
        "token_id": token_id,
        "path": str(path),
        "n_events": int(len(events)),
        "content_hash": h,
        "publish_lag_days": publish_lag_days,
        "source": "polymarket_clob_prices_history",
        "first_event": str(events["event_time"].iloc[0]),
        "last_event": str(events["event_time"].iloc[-1]),
        **(meta_extra or {}),
    }
    (out_dir / f"{series_id}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta
