"""Versioned aggregate DeFi TVL series (research only)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.data.sources.defillama_tvl import DefiTvlError
from crl.shared.reproducibility import file_sha256


def validate_tvl_events(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise DefiTvlError("tvl events empty")
    out = df.copy()
    if "event_time" not in out.columns or "tvl_usd" not in out.columns:
        raise DefiTvlError("need event_time and tvl_usd")
    out["event_time"] = pd.to_datetime(out["event_time"], utc=True)
    out["tvl_usd"] = pd.to_numeric(out["tvl_usd"], errors="coerce")
    out = out.dropna(subset=["tvl_usd"])
    out = out.loc[out["tvl_usd"] > 0].sort_values("event_time")
    if out["event_time"].duplicated().any():
        out = out.drop_duplicates(subset=["event_time"], keep="last")
    return out.reset_index(drop=True)


def tvl_events_hash(df: pd.DataFrame) -> str:
    v = validate_tvl_events(df)
    payload = v[["event_time", "tvl_usd"]].copy()
    payload["event_time"] = payload["event_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    return hashlib.sha256(payload.to_csv(index=False).encode()).hexdigest()


def save_tvl_series(
    df: pd.DataFrame,
    *,
    processed_dir: Path,
    publish_lag_days: int = 1,
    source: str = "defillama_tvl",
) -> dict[str, Any]:
    v = validate_tvl_events(df)
    processed_dir.mkdir(parents=True, exist_ok=True)
    sha = tvl_events_hash(v)
    series_id = f"{source}_agg_usd_lag{publish_lag_days}_{sha[:12]}"
    path = processed_dir / f"{series_id}.parquet"
    meta_path = processed_dir / f"{series_id}.json"
    if not path.exists():
        v.to_parquet(path, index=False)
    meta = {
        "series_id": series_id,
        "source": source,
        "property_id": "defi_agg_tvl",
        "publish_lag_days": publish_lag_days,
        "sha256_content": sha,
        "sha256_file": file_sha256(path),
        "row_count": len(v),
        "start": str(v["event_time"].iloc[0]),
        "end": str(v["event_time"].iloc[-1]),
        "path": str(path),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "note": "Aggregate DeFi TVL — research characterization only",
        "attribution": "DefiLlama charts API (https://defillama.com)",
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def load_latest_tvl(processed_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed_dir = Path(processed_dir)
    metas = sorted(
        processed_dir.glob("defillama_tvl_agg_usd_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not metas:
        raise DefiTvlError("no TVL series; run: crl observe fetch-defi-tvl")
    meta = json.loads(metas[0].read_text())
    path = Path(meta["path"])
    if not path.exists():
        path = processed_dir / path.name
    return validate_tvl_events(pd.read_parquet(path)), meta
