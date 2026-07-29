"""Versioned aggregate stablecoin supply series (research only)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.data.sources.defillama_stablecoins import StablecoinSupplyError
from crl.shared.reproducibility import file_sha256


def validate_supply_events(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise StablecoinSupplyError("supply events empty")
    out = df.copy()
    if "event_time" not in out.columns or "supply_usd" not in out.columns:
        raise StablecoinSupplyError("need event_time and supply_usd")
    out["event_time"] = pd.to_datetime(out["event_time"], utc=True)
    out["supply_usd"] = pd.to_numeric(out["supply_usd"], errors="coerce")
    out = out.dropna(subset=["supply_usd"]).sort_values("event_time")
    if out["event_time"].duplicated().any():
        out = out.drop_duplicates(subset=["event_time"], keep="last")
    if (out["supply_usd"] <= 0).any():
        out = out.loc[out["supply_usd"] > 0]
    return out.reset_index(drop=True)


def supply_events_hash(df: pd.DataFrame) -> str:
    v = validate_supply_events(df)
    payload = v[["event_time", "supply_usd"]].copy()
    payload["event_time"] = payload["event_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    return hashlib.sha256(payload.to_csv(index=False).encode()).hexdigest()


def save_supply_series(
    df: pd.DataFrame,
    *,
    processed_dir: Path,
    source: str = "defillama_stablecoins",
    publish_lag_days: int = 1,
) -> dict[str, Any]:
    v = validate_supply_events(df)
    processed_dir.mkdir(parents=True, exist_ok=True)
    sha = supply_events_hash(v)
    series_id = f"{source}_agg_supply_usd_lag{publish_lag_days}_{sha[:12]}"
    path = processed_dir / f"{series_id}.parquet"
    meta_path = processed_dir / f"{series_id}.json"
    if not path.exists():
        v.to_parquet(path, index=False)
    meta = {
        "series_id": series_id,
        "source": source,
        "property_id": "stablecoin_agg_supply",
        "publish_lag_days": publish_lag_days,
        "sha256_content": sha,
        "sha256_file": file_sha256(path),
        "row_count": len(v),
        "start": str(v["event_time"].iloc[0]),
        "end": str(v["event_time"].iloc[-1]),
        "path": str(path),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "note": "Aggregate stablecoin circulating USD — research characterization only",
        "attribution": "DefiLlama stablecoins API (https://defillama.com)",
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def load_latest_supply(processed_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed_dir = Path(processed_dir)
    metas = sorted(
        processed_dir.glob("defillama_stablecoins_agg_supply_usd_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not metas:
        raise StablecoinSupplyError(
            "no supply series; run: crl observe fetch-stable-supply"
        )
    meta = json.loads(metas[0].read_text())
    path = Path(meta["path"])
    if not path.exists():
        path = processed_dir / path.name
    return validate_supply_events(pd.read_parquet(path)), meta
