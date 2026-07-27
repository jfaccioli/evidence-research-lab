"""Frozen feature matrix cache keyed by dataset_id + feature schema version."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from crl.research.regimes.labels import add_regime_labels
from crl.shared.data.features import add_features
from crl.shared.data.funding import add_funding_features, funding_events_content_hash
from crl.shared.data.oi import add_oi_features, oi_events_content_hash
from crl.shared.reproducibility import file_sha256

FEATURE_SCHEMA_VERSION = "features_v3_donchian_mom"
FEATURE_SCHEMA_VERSION_FUNDING = "features_v4_funding_pit_v1"
FEATURE_SCHEMA_VERSION_OI = "features_v4_oi_pit_v1"
FEATURE_SCHEMA_VERSION_FUNDING_OI = "features_v4_funding_oi_pit_v1"


def feature_cache_path(
    cache_dir: Path,
    dataset_id: str,
    *,
    schema_version: str = FEATURE_SCHEMA_VERSION,
) -> Path:
    return cache_dir / f"{dataset_id}__{schema_version}.parquet"


def load_or_build_features(
    ohlcv: pd.DataFrame,
    *,
    dataset_id: str,
    cache_dir: Path,
    force: bool = False,
    funding_events: Optional[pd.DataFrame] = None,
    funding_series_id: Optional[str] = None,
    oi_events: Optional[pd.DataFrame] = None,
    oi_series_id: Optional[str] = None,
) -> pd.DataFrame:
    """Build causal features+regimes once per dataset; reuse across batch hyps.

    Optional PIT series (funding / OI) are as-of joined at bar close and
    included in the cache key so series identity is frozen.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    schema = FEATURE_SCHEMA_VERSION
    ds_key = dataset_id
    parts: list[str] = []
    if funding_events is not None:
        fhash = funding_events_content_hash(funding_events)
        sid = (funding_series_id or fhash[:12]).strip()
        parts.append(f"fund_{sid}")
    if oi_events is not None:
        ohash = oi_events_content_hash(oi_events)
        sid = (oi_series_id or ohash[:12]).strip()
        parts.append(f"oi_{sid}")
    if funding_events is not None and oi_events is not None:
        schema = FEATURE_SCHEMA_VERSION_FUNDING_OI
    elif funding_events is not None:
        schema = FEATURE_SCHEMA_VERSION_FUNDING
    elif oi_events is not None:
        schema = FEATURE_SCHEMA_VERSION_OI
    if parts:
        ds_key = f"{dataset_id}__" + "__".join(parts)
    path = feature_cache_path(cache_dir, ds_key, schema_version=schema)
    if path.exists() and not force:
        feat = pd.read_parquet(path)
        if not isinstance(feat.index, pd.DatetimeIndex):
            feat.index = pd.to_datetime(feat.index, utc=True)
        elif feat.index.tz is None:
            feat.index = feat.index.tz_localize("UTC")
        return feat

    feat = add_regime_labels(add_features(ohlcv))
    if funding_events is not None:
        feat = add_funding_features(feat, funding_events)
    if oi_events is not None:
        feat = add_oi_features(feat, oi_events)
    feat.to_parquet(path)
    # sidecar hash for integrity
    (path.with_suffix(".sha256")).write_text(file_sha256(path))
    return feat
