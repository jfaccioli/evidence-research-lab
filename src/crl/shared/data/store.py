"""Versioned parquet store + manifests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.shared.data.trust import TrustFactors, score_trust
from crl.shared.reproducibility import file_sha256
from crl.shared.types import DataManifest


def validate_ohlcv(df: pd.DataFrame) -> tuple[float, float, float]:
    """Return (completeness, mono, ohlc_consistency) factors in [0,1]."""
    if df.empty:
        return 0.0, 0.0, 0.0
    completeness = 1.0 - float(df[["open", "high", "low", "close", "volume"]].isna().any(axis=1).mean())
    mono = 1.0 if df.index.is_monotonic_increasing and not df.index.has_duplicates else 0.5
    ok = (
        (df["low"] <= df["open"])
        & (df["low"] <= df["close"])
        & (df["high"] >= df["open"])
        & (df["high"] >= df["close"])
        & (df["high"] >= df["low"])
    )
    ohlc = float(ok.mean())
    return completeness, mono, ohlc


def make_dataset_id(source: str, symbol: str, interval: str, sha: str) -> str:
    return f"{source}_{symbol}_{interval}_{sha[:12]}"


def save_dataset(
    df: pd.DataFrame,
    *,
    source: str,
    symbol: str,
    interval: str,
    processed_dir: Path,
    manifest_dir: Path,
    source_class: str | None = None,
) -> DataManifest:
    processed_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    completeness, mono, ohlc = validate_ohlcv(df)
    years = 0.0
    if len(df) > 1:
        years = (df.index[-1] - df.index[0]).total_seconds() / (365.25 * 24 * 3600)

    trust = score_trust(
        TrustFactors(
            source_class=source_class or source,
            completeness=completeness,
            timestamp_monotonic=mono,
            ohlc_consistency=ohlc,
            history_depth_years=years,
        )
    )

    # Temporary path for hashing content
    tmp_name = f"{source}_{symbol}_{interval}_tmp.parquet"
    tmp_path = processed_dir / tmp_name
    df.to_parquet(tmp_path)
    sha = file_sha256(tmp_path)
    dataset_id = make_dataset_id(source, symbol, interval, sha)
    final_path = processed_dir / f"{dataset_id}.parquet"
    if final_path.exists():
        tmp_path.unlink(missing_ok=True)
    else:
        tmp_path.rename(final_path)

    manifest = DataManifest(
        dataset_id=dataset_id,
        source=source,
        symbol=symbol,
        interval=interval,
        start=str(df.index[0]),
        end=str(df.index[-1]),
        row_count=len(df),
        sha256=sha,
        trust_score=trust,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        path=str(final_path),
    )
    mpath = manifest_dir / f"{dataset_id}.json"
    mpath.write_text(manifest.model_dump_json(indent=2))
    return manifest


def load_dataset(
    manifest_or_id: str | Path,
    manifest_dir: Path | None = None,
    *,
    verify_hash: bool = True,
) -> tuple[pd.DataFrame, DataManifest]:
    p = Path(manifest_or_id)
    if p.suffix == ".json" and p.exists():
        manifest = DataManifest.model_validate_json(p.read_text())
    else:
        # dataset_id
        if manifest_dir is None:
            raise ValueError("manifest_dir required when loading by dataset_id")
        mpath = manifest_dir / f"{manifest_or_id}.json"
        if not mpath.exists():
            # try as direct parquet path
            if Path(manifest_or_id).suffix == ".parquet":
                df = pd.read_parquet(manifest_or_id)
                dummy = DataManifest(
                    dataset_id=Path(manifest_or_id).stem,
                    source="unknown",
                    symbol="?",
                    interval="?",
                    start=str(df.index[0]),
                    end=str(df.index[-1]),
                    row_count=len(df),
                    sha256="",
                    trust_score=0.5,
                    fetched_at="",
                    path=str(manifest_or_id),
                )
                return df, dummy
            raise FileNotFoundError(f"Manifest not found: {mpath}")
        manifest = DataManifest.model_validate_json(mpath.read_text())

    path = Path(manifest.path)
    if verify_hash and manifest.sha256:
        actual = file_sha256(path)
        if actual != manifest.sha256:
            raise ValueError(
                f"Data integrity failure for {manifest.dataset_id}: "
                f"manifest sha256={manifest.sha256[:12]}… actual={actual[:12]}…"
            )

    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)
    elif df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df, manifest


def latest_manifest(manifest_dir: Path, symbol: str, interval: str, source: str = "binance_public") -> DataManifest | None:
    if not manifest_dir.exists():
        return None
    cands: list[DataManifest] = []
    for p in manifest_dir.glob("*.json"):
        try:
            m = DataManifest.model_validate_json(p.read_text())
        except Exception:
            continue
        if m.symbol == symbol and m.interval == interval and m.source == source:
            cands.append(m)
    if not cands:
        return None
    cands.sort(key=lambda m: m.fetched_at, reverse=True)
    return cands[0]
