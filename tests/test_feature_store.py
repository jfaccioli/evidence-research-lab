from pathlib import Path

from crl.shared.data.feature_store import FEATURE_SCHEMA_VERSION, load_or_build_features
from crl.shared.data.sources.mock import MockOHLCVSource


def test_feature_cache_roundtrip(tmp_path: Path):
    df = MockOHLCVSource(n=300, seed=0).fetch_ohlcv("BTCUSDT", "1d")
    a = load_or_build_features(df, dataset_id="mock1", cache_dir=tmp_path)
    b = load_or_build_features(df, dataset_id="mock1", cache_dir=tmp_path)
    assert list(a.columns) == list(b.columns)
    assert len(a) == len(b)
    assert FEATURE_SCHEMA_VERSION in str(list(tmp_path.glob("*.parquet"))[0])
