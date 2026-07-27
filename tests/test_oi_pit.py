"""OI PIT join rules and causal features (programme OI v1 scaffold)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crl.shared.data.oi import (
    OIPITError,
    add_oi_features,
    asof_oi_at_bar_close,
    assert_oi_no_lookahead,
    oi_events_content_hash,
    validate_oi_events,
)
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.data.sources.oi_mock import generate_mock_oi_events


def test_validate_and_hash_stable():
    ev = generate_mock_oi_events(start="2020-01-01", end="2020-02-01", seed=1)
    h1 = oi_events_content_hash(ev)
    h2 = oi_events_content_hash(ev)
    assert h1 == h2
    assert len(h1) == 64


def test_duplicate_oi_time_rejected():
    ev = pd.DataFrame(
        {
            "oi_time": pd.to_datetime(
                ["2020-01-01", "2020-01-01"], utc=True
            ),
            "open_interest": [1e9, 1.1e9],
        }
    )
    with pytest.raises(OIPITError, match="duplicate"):
        validate_oi_events(ev)


def test_negative_oi_rejected():
    ev = pd.DataFrame(
        {
            "oi_time": pd.to_datetime(["2020-01-01"], utc=True),
            "open_interest": [-1.0],
        }
    )
    with pytest.raises(OIPITError, match="non-negative"):
        validate_oi_events(ev)


def test_asof_never_uses_future_event():
    bars = pd.DatetimeIndex(
        [pd.Timestamp("2020-01-01 12:00", tz="UTC")], name="timestamp"
    )
    ev = pd.DataFrame(
        {
            "oi_time": pd.to_datetime(
                ["2020-01-01 08:00", "2020-01-01 16:00"], utc=True
            ),
            "open_interest": [1.0e9, 2.0e9],
        }
    )
    asof = asof_oi_at_bar_close(bars, ev)
    assert float(asof["oi_last"].iloc[0]) == pytest.approx(1.0e9)
    assert pd.Timestamp(asof["oi_time_used"].iloc[0]) == pd.Timestamp(
        "2020-01-01 08:00", tz="UTC"
    )


def test_add_oi_features_no_lookahead_on_mock_ohlcv():
    src = MockOHLCVSource()
    ohlcv = src.fetch_ohlcv("BTCUSDT", "1d", limit=400)
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + pd.Timedelta(days=1)).date())
    ev = generate_mock_oi_events(start=start, end=end, seed=7)
    out = add_oi_features(ohlcv, ev)
    for col in (
        "oi_last",
        "oi_z_60",
        "oi_high",
        "oi_rising",
        "oi_falling",
        "oi_chg_pct_high",
        "oi_sum5_high",
    ):
        assert col in out.columns
    assert_oi_no_lookahead(out, ev, sample=100)
    # Future spike must not leak into earlier bars
    ev2 = ev.copy()
    late = ev2["oi_time"].max() + pd.Timedelta(days=30)
    ev2 = pd.concat(
        [
            ev2,
            pd.DataFrame({"oi_time": [late], "open_interest": [9.99e12]}),
        ],
        ignore_index=True,
    )
    out2 = add_oi_features(ohlcv, ev2)
    mask = ohlcv.index < late
    pd.testing.assert_series_equal(
        out.loc[mask, "oi_last"],
        out2.loc[mask, "oi_last"],
        check_names=False,
    )


def test_pre_registered_oi_hyps_count_and_parse():
    import yaml

    d = Path("examples/batch/oi")
    files = sorted(d.glob("hyp_oi_*.yaml"))
    assert len(files) == 10
    for f in files:
        raw = yaml.safe_load(f.read_text())
        assert raw["taxonomy"] == "open_interest"
        assert "oi_pit_v1" in raw.get("feature_tags", [])
        assert "expression" in raw["entry"]


def test_offline_binance_oi_fixture_parses_and_asof():
    import json

    from crl.shared.data.sources.binance_oi import events_from_binance_oi_json_records

    path = Path("tests/fixtures/binance_btcusdt_oi_sample.json")
    if not path.exists():
        pytest.skip("offline fixture missing")
    records = json.loads(path.read_text())
    ev = events_from_binance_oi_json_records(records)
    assert len(ev) == len(records)
    bars = pd.date_range(ev["oi_time"].iloc[0], periods=5, freq="1D", tz="UTC")
    asof = asof_oi_at_bar_close(bars, ev)
    assert asof["oi_last"].notna().any()


def test_bybit_fixture_parse():
    import json

    from crl.shared.data.sources.bybit_oi import events_from_bybit_json_records

    records = [
        {"openInterest": "100.5", "timestamp": "1609459200000"},
        {"openInterest": "101.0", "timestamp": "1609545600000"},
    ]
    ev = events_from_bybit_json_records(records)
    assert len(ev) == 2
    assert float(ev["open_interest"].iloc[0]) == 100.5


def test_feature_store_oi_cache_key(tmp_path: Path):
    from crl.shared.data.feature_store import (
        FEATURE_SCHEMA_VERSION_OI,
        load_or_build_features,
    )

    ohlcv = MockOHLCVSource(n=250, seed=0).fetch_ohlcv("BTCUSDT", "1d")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + pd.Timedelta(days=1)).date())
    ev = generate_mock_oi_events(start=start, end=end, seed=3)
    feat = load_or_build_features(
        ohlcv,
        dataset_id="mock_oi",
        cache_dir=tmp_path,
        force=True,
        oi_events=ev,
        oi_series_id="mock3",
    )
    assert "oi_last" in feat.columns
    assert any(FEATURE_SCHEMA_VERSION_OI in p.name for p in tmp_path.glob("*.parquet"))
