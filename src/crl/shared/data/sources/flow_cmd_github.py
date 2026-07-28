"""BTC exchange netflow from free public GitHub mirror (CC BY 4.0).

Source: https://github.com/ErcinDedeoglu/crypto-market-data
  data/daily/btc_exchange_netflow.json

Attribution (mandatory under CC BY 4.0):
  Crypto market data provided by Crypto Market Data by Ercin Dedeoglu.

PIT policy (binding for this adapter)
-------------------------------------
Commercial exchange-flow series are often **revision-mutable**. The mirror exposes
``last_modified`` that can lag the calendar day by months/years (bulk rewrite),
so using raw ``last_modified`` as ``flow_time`` would either:
  - destroy early sample (all points appear only at bulk-write time), or
  - require a full revision journal we do not have.

Therefore this adapter uses a **conservative fixed publish lag**:
  observation calendar day D (UTC) → flow_time = D 23:59:59 UTC + publish_lag_days

Default ``publish_lag_days=1`` means the day-D netflow is available for decisions
only after the next UTC day completes (no same-day look-ahead).

This is an approximation for free exploratory science — **not** vendor-grade PIT.
Label series_id with ``cmd_`` prefix; mock remains forbidden for promotion.

Sign: positive value = net into exchanges (matches lab convention).
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.config import project_root
from crl.shared.data.flow import flow_events_content_hash, validate_flow_events

DEFAULT_URL = (
    "https://raw.githubusercontent.com/ErcinDedeoglu/crypto-market-data/"
    "main/data/daily/btc_exchange_netflow.json"
)
SERIES_ID = "cmd_btc_exchange_netflow_v1"
ATTRIBUTION = (
    "Crypto market data provided by Crypto Market Data "
    "(https://github.com/ErcinDedeoglu/crypto-market-data) by Ercin Dedeoglu. CC BY 4.0."
)


def fetch_cmd_netflow_json(url: str = DEFAULT_URL, timeout: float = 120.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "evidence-research-lab/crl"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_json_to_flow_events(
    payload: dict[str, Any],
    *,
    publish_lag_days: int = 1,
) -> pd.DataFrame:
    """Convert CMD daily series to flow_time / net_flow with fixed publish lag."""
    if publish_lag_days < 0:
        raise ValueError("publish_lag_days must be >= 0")
    rows = payload.get("data") or []
    if not rows:
        raise ValueError("CMD netflow payload empty")
    out_rows: list[dict[str, Any]] = []
    for r in rows:
        ts_ms = int(r["timestamp"])
        day = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # End of observation day + lag days
        flow_time = day + timedelta(days=1) - timedelta(seconds=1)  # 23:59:59 D
        flow_time = flow_time + timedelta(days=int(publish_lag_days))
        out_rows.append(
            {
                "flow_time": flow_time,
                "net_flow": float(r["value"]),
                "obs_day": day.isoformat(),
            }
        )
    df = pd.DataFrame(out_rows)
    # Keep only required columns for validate; obs_day dropped after
    core = df[["flow_time", "net_flow"]].copy()
    # De-dupe if any
    core = core.drop_duplicates(subset=["flow_time"], keep="last")
    return validate_flow_events(core)


def ingest_cmd_btc_netflow(
    *,
    out_dir: Path | None = None,
    url: str = DEFAULT_URL,
    publish_lag_days: int = 1,
    series_id: str = SERIES_ID,
) -> dict[str, Any]:
    """Fetch, convert, write parquet under data/processed/flow/, return meta."""
    root = project_root()
    out_dir = out_dir or (root / "data" / "processed" / "flow")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = fetch_cmd_netflow_json(url)
    events = cmd_json_to_flow_events(payload, publish_lag_days=publish_lag_days)
    path = out_dir / f"{series_id}.parquet"
    events.to_parquet(path, index=False)
    h = flow_events_content_hash(events)
    meta = {
        "series_id": series_id,
        "path": str(path),
        "n_events": int(len(events)),
        "content_hash": h,
        "publish_lag_days": publish_lag_days,
        "source_url": url,
        "attribution": ATTRIBUTION,
        "first_flow_time": str(events["flow_time"].iloc[0]),
        "last_flow_time": str(events["flow_time"].iloc[-1]),
        "pit_note": (
            "Fixed publish_lag_days applied; vendor last_modified revisions not "
            "point-in-time recoverable from this mirror."
        ),
    }
    (out_dir / f"{series_id}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta
