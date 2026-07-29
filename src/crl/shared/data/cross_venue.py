"""Cross-venue basis series versioning (research only)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.reproducibility import file_sha256


class CrossVenueError(ValueError):
    pass


def validate_basis_events(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise CrossVenueError("basis events empty")
    out = df.copy()
    need = {"event_time", "basis"}
    if missing := need - set(out.columns):
        raise CrossVenueError(f"missing {missing}")
    out["event_time"] = pd.to_datetime(out["event_time"], utc=True)
    out["basis"] = pd.to_numeric(out["basis"], errors="coerce")
    out = out.dropna(subset=["basis"]).sort_values("event_time")
    if out["event_time"].duplicated().any():
        out = out.drop_duplicates(subset=["event_time"], keep="last")
    return out.reset_index(drop=True)


def basis_events_hash(df: pd.DataFrame) -> str:
    v = validate_basis_events(df)
    payload = v[["event_time", "basis"]].copy()
    payload["event_time"] = payload["event_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    return hashlib.sha256(payload.to_csv(index=False).encode()).hexdigest()


def save_basis_series(
    df: pd.DataFrame,
    *,
    processed_dir: Path,
    venues: str = "binance_usdt_vs_coinbase_usd",
) -> dict[str, Any]:
    v = validate_basis_events(df)
    processed_dir.mkdir(parents=True, exist_ok=True)
    sha = basis_events_hash(v)
    series_id = f"cross_venue_{venues}_{sha[:12]}"
    path = processed_dir / f"{series_id}.parquet"
    meta_path = processed_dir / f"{series_id}.json"
    if not path.exists():
        v.to_parquet(path, index=False)
    meta = {
        "series_id": series_id,
        "source": "cross_venue_basis",
        "property_id": "cross_venue_basis",
        "venues": venues,
        "definition": "log(binance_close_USDT / coinbase_close_USD)",
        "sha256_content": sha,
        "sha256_file": file_sha256(path),
        "row_count": len(v),
        "start": str(v["event_time"].iloc[0]),
        "end": str(v["event_time"].iloc[-1]),
        "path": str(path),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "pit_note": (
            "Same UTC calendar day closes; lag-1 for predictive use; "
            "USD vs USDT not FX-adjusted (part of measured dislocation)"
        ),
        "note": "Research characterization only — not a trading signal",
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def load_latest_basis(processed_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed_dir = Path(processed_dir)
    metas = sorted(
        processed_dir.glob("cross_venue_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not metas:
        raise CrossVenueError("no basis series; run: crl observe fetch-cross-basis")
    meta = json.loads(metas[0].read_text())
    path = Path(meta["path"])
    if not path.exists():
        path = processed_dir / path.name
    return validate_basis_events(pd.read_parquet(path)), meta
