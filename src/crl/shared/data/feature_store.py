"""Frozen feature matrix cache keyed by dataset_id + feature schema version."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crl.research.regimes.labels import add_regime_labels
from crl.shared.data.features import add_features
from crl.shared.reproducibility import file_sha256

FEATURE_SCHEMA_VERSION = "features_v3_donchian_mom"


def feature_cache_path(cache_dir: Path, dataset_id: str) -> Path:
    return cache_dir / f"{dataset_id}__{FEATURE_SCHEMA_VERSION}.parquet"


def load_or_build_features(
    ohlcv: pd.DataFrame,
    *,
    dataset_id: str,
    cache_dir: Path,
    force: bool = False,
) -> pd.DataFrame:
    """Build causal features+regimes once per dataset; reuse across batch hyps."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = feature_cache_path(cache_dir, dataset_id)
    if path.exists() and not force:
        feat = pd.read_parquet(path)
        if not isinstance(feat.index, pd.DatetimeIndex):
            feat.index = pd.to_datetime(feat.index, utc=True)
        elif feat.index.tz is None:
            feat.index = feat.index.tz_localize("UTC")
        return feat

    feat = add_regime_labels(add_features(ohlcv))
    feat.to_parquet(path)
    # sidecar hash for integrity
    (path.with_suffix(".sha256")).write_text(file_sha256(path))
    return feat
