"""Funding PIT join rules and causal features (programme funding v1)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crl.shared.data.funding import (
    FundingPITError,
    add_funding_features,
    asof_funding_at_bar_close,
    assert_funding_no_lookahead,
    funding_events_content_hash,
    validate_funding_events,
)
from crl.shared.data.sources.funding_mock import generate_mock_funding_events
from crl.shared.data.sources.mock import MockOHLCVSource


def test_validate_and_hash_stable():
    ev = generate_mock_funding_events(start="2020-01-01", end="2020-02-01", seed=1)
    h1 = funding_events_content_hash(ev)
    h2 = funding_events_content_hash(ev)
    assert h1 == h2
    assert len(h1) == 64


def test_duplicate_funding_time_rejected():
    ev = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(
                ["2020-01-01", "2020-01-01"], utc=True
            ),
            "funding_rate": [0.01, 0.02],
        }
    )
    with pytest.raises(FundingPITError, match="duplicate"):
        validate_funding_events(ev)


def test_asof_never_uses_future_event():
    # Bar at 12:00; events at 08:00 (rate 1) and 16:00 (rate 2)
    bars = pd.DatetimeIndex(
        [pd.Timestamp("2020-01-01 12:00", tz="UTC")], name="timestamp"
    )
    ev = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(
                ["2020-01-01 08:00", "2020-01-01 16:00"], utc=True
            ),
            "funding_rate": [0.001, 0.009],
        }
    )
    asof = asof_funding_at_bar_close(bars, ev)
    assert float(asof["funding_last"].iloc[0]) == pytest.approx(0.001)
    assert pd.Timestamp(asof["funding_time_used"].iloc[0]) == pd.Timestamp(
        "2020-01-01 08:00", tz="UTC"
    )


def test_add_funding_features_no_lookahead_on_mock_ohlcv():
    src = MockOHLCVSource()
    # Prefer public API if available
    if hasattr(src, "fetch_ohlcv"):
        ohlcv = src.fetch_ohlcv("BTCUSDT", "1d", limit=400)
    else:
        pytest.skip("MockOHLCVSource API mismatch")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + pd.Timedelta(days=1)).date())
    ev = generate_mock_funding_events(start=start, end=end, seed=7)
    out = add_funding_features(ohlcv, ev)
    assert "funding_last" in out.columns
    assert "funding_z_60" in out.columns
    assert "funding_high" in out.columns
    assert_funding_no_lookahead(out, ev, sample=100)
    # Future event must not leak: force a huge late rate and ensure early bars unchanged
    ev2 = ev.copy()
    late = ev2["funding_time"].max() + pd.Timedelta(days=30)
    ev2 = pd.concat(
        [
            ev2,
            pd.DataFrame({"funding_time": [late], "funding_rate": [9.99]}),
        ],
        ignore_index=True,
    )
    out2 = add_funding_features(ohlcv, ev2)
    # bars before late event should match original funding_last
    mask = ohlcv.index < late
    pd.testing.assert_series_equal(
        out.loc[mask, "funding_last"],
        out2.loc[mask, "funding_last"],
        check_names=False,
    )


def test_pre_registered_funding_hyps_count_and_parse():
    import yaml
    from pathlib import Path

    d = Path("examples/batch/funding")
    files = sorted(d.glob("hyp_funding_*.yaml"))
    assert len(files) == 10
    for f in files:
        raw = yaml.safe_load(f.read_text())
        assert raw["taxonomy"] == "funding_proxy"
        assert "funding_pit_v1" in raw.get("feature_tags", [])
        assert "expression" in raw["entry"]


def test_offline_binance_fixture_parses_and_asof():
    import json
    from pathlib import Path

    from crl.shared.data.sources.binance_funding import events_from_binance_json_records

    path = Path("tests/fixtures/binance_btcusdt_funding_sample.json")
    if not path.exists():
        pytest.skip("offline fixture missing")
    records = json.loads(path.read_text())
    ev = events_from_binance_json_records(records)
    assert len(ev) == len(records)
    bars = pd.date_range(ev["funding_time"].iloc[0], periods=10, freq="1D", tz="UTC")
    asof = asof_funding_at_bar_close(bars, ev)
    assert asof["funding_last"].notna().any()
