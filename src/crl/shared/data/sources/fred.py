"""FRED (St. Louis Fed) public series download — free API key from .env.

Does not log or commit secrets. Snapshot download (not ALFRED vintage reconstruction).
"""

from __future__ import annotations

import json
import os
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

FRED_OBS_URL = "https://api.stlouisfed.org/fred/series/observations"


def load_fred_api_key(env_path: Path | None = None) -> str:
    """Load FRED_API_KEY from environment or project .env (gitignored)."""
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        return key
    path = env_path or (project_root() / ".env")
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "FRED_API_KEY":
                key = v.strip().strip('"').strip("'")
                if key:
                    return key
    raise RuntimeError(
        "FRED_API_KEY not set. Add it to .env (gitignored) or export FRED_API_KEY=..."
    )


def fetch_fred_observations(
    series_id: str,
    *,
    api_key: str | None = None,
    observation_start: str = "2000-01-01",
) -> pd.DataFrame:
    """Return DataFrame columns: date (UTC midnight), value (float)."""
    key = api_key or load_fred_api_key()
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "observation_start": observation_start,
        "sort_order": "asc",
    }
    url = FRED_OBS_URL + "?" + urllib.parse.urlencode(params)
    # Do not put api_key in logs
    req = urllib.request.Request(
        url, headers={"User-Agent": "evidence-research-lab/crl-fred"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    obs = payload.get("observations") or []
    rows = []
    for o in obs:
        val = o.get("value")
        if val in (".", "", None):
            continue
        try:
            v = float(val)
        except ValueError:
            continue
        d = pd.Timestamp(o["date"], tz="UTC")
        rows.append({"date": d, "value": v})
    if not rows:
        raise RuntimeError(f"No numeric observations for FRED {series_id}")
    return pd.DataFrame(rows)


def observations_to_events(
    obs: pd.DataFrame,
    *,
    publish_lag_days: int = 1,
) -> pd.DataFrame:
    """FRED date D → event_time = end of D + publish_lag_days (UTC)."""
    if publish_lag_days < 0:
        raise ValueError("publish_lag_days must be >= 0")
    rows = []
    for _, r in obs.iterrows():
        d = pd.Timestamp(r["date"]).tz_convert("UTC").normalize()
        # end of observation calendar day + lag days
        event_time = d + timedelta(days=1) - timedelta(seconds=1) + timedelta(
            days=int(publish_lag_days)
        )
        rows.append({"event_time": event_time, "value": float(r["value"])})
    return validate_external_events(pd.DataFrame(rows))


def ingest_fred_series(
    series_id: str,
    *,
    publish_lag_days: int = 1,
    observation_start: str = "2000-01-01",
    out_id: str | None = None,
) -> dict[str, Any]:
    """Download, lag, hash, write data/processed/external/fred_<id>_lagN.parquet."""
    root = project_root()
    out_dir = root / "data" / "processed" / "external"
    out_dir.mkdir(parents=True, exist_ok=True)
    obs = fetch_fred_observations(series_id, observation_start=observation_start)
    events = observations_to_events(obs, publish_lag_days=publish_lag_days)
    sid = out_id or f"fred_{series_id.lower()}_lag{publish_lag_days}_v1"
    path = out_dir / f"{sid}.parquet"
    events.to_parquet(path, index=False)
    h = external_events_hash(events)
    meta = {
        "series_id": sid,
        "fred_id": series_id,
        "publish_lag_days": publish_lag_days,
        "n_events": int(len(events)),
        "content_hash": h,
        "path": str(path),
        "first_event": str(events["event_time"].iloc[0]),
        "last_event": str(events["event_time"].iloc[-1]),
        "pit_note": (
            "Snapshot download; not ALFRED vintage reconstruction. "
            "event_time = FRED date end-of-day + publish_lag_days."
        ),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / f"{sid}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta
