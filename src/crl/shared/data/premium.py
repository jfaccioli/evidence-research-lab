"""Perpetual premium series: versioning + helpers (research data only)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.data.sources.binance_premium import PremiumPITError
from crl.shared.reproducibility import file_sha256


def validate_premium_events(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise PremiumPITError("premium events empty")
    out = df.copy()
    need = {"event_time", "premium_close"}
    missing = need - set(out.columns)
    if missing:
        raise PremiumPITError(f"missing columns {missing}")
    out["event_time"] = pd.to_datetime(out["event_time"], utc=True)
    out["premium_close"] = pd.to_numeric(out["premium_close"], errors="coerce")
    if out["premium_close"].isna().all():
        raise PremiumPITError("premium_close all missing")
    out = out.sort_values("event_time")
    if out["event_time"].duplicated().any():
        out = out.drop_duplicates(subset=["event_time"], keep="last")
    return out.reset_index(drop=True)


def premium_events_hash(df: pd.DataFrame) -> str:
    v = validate_premium_events(df)
    payload = v[["event_time", "premium_close"]].copy()
    payload["event_time"] = payload["event_time"].map(
        lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    return hashlib.sha256(payload.to_csv(index=False).encode()).hexdigest()


def save_premium_series(
    df: pd.DataFrame,
    *,
    symbol: str,
    interval: str,
    processed_dir: Path,
    source: str = "binance_premium",
) -> dict[str, Any]:
    """Write versioned premium parquet + sidecar json under processed/premium/."""
    v = validate_premium_events(df)
    processed_dir.mkdir(parents=True, exist_ok=True)
    sha = premium_events_hash(v)
    series_id = f"{source}_{symbol}_premium_{interval}_{sha[:12]}"
    path = processed_dir / f"{series_id}.parquet"
    meta_path = processed_dir / f"{series_id}.json"
    if not path.exists():
        v.to_parquet(path, index=False)
    # Re-hash file for storage integrity
    fsha = file_sha256(path)
    meta = {
        "series_id": series_id,
        "source": source,
        "symbol": symbol,
        "interval": interval,
        "sha256_content": sha,
        "sha256_file": fsha,
        "row_count": len(v),
        "start": str(v["event_time"].iloc[0]),
        "end": str(v["event_time"].iloc[-1]),
        "path": str(path),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "property_id": "perp_premium",
        "note": "Research series only — not a trading signal",
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def load_latest_premium(
    processed_dir: Path,
    *,
    symbol: str = "BTCUSDT",
    interval: str = "1d",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load newest matching premium series by mtime of meta json."""
    processed_dir = Path(processed_dir)
    if not processed_dir.exists():
        raise PremiumPITError(f"no premium dir {processed_dir}")
    metas = sorted(
        processed_dir.glob(f"binance_premium_{symbol}_premium_{interval}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not metas:
        raise PremiumPITError(
            f"no premium series for {symbol} {interval}; run: crl observe fetch-premium"
        )
    meta = json.loads(metas[0].read_text())
    path = Path(meta["path"])
    if not path.is_absolute():
        # relative to project-ish
        path = processed_dir / path.name
    df = pd.read_parquet(path)
    return validate_premium_events(df), meta
