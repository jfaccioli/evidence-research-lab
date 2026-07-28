"""Flow PIT join rules and causal features (whale/flow scaffold)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from crl.shared.data.flow import (
    FlowPITError,
    add_flow_features,
    asof_flow_at_bar_close,
    assert_flow_no_lookahead,
    flow_events_content_hash,
    validate_flow_events,
)
from crl.shared.data.sources.flow_mock import generate_mock_flow_events
from crl.shared.data.sources.mock import MockOHLCVSource


def test_validate_and_hash_stable():
    ev = generate_mock_flow_events(start="2020-01-01", end="2020-03-01", seed=1)
    h1 = flow_events_content_hash(ev)
    assert h1 == flow_events_content_hash(ev)
    assert len(h1) == 64


def test_duplicate_flow_time_rejected():
    ev = pd.DataFrame(
        {
            "flow_time": pd.to_datetime(["2020-01-01", "2020-01-01"], utc=True),
            "net_flow": [1.0, 2.0],
        }
    )
    with pytest.raises(FlowPITError, match="duplicate"):
        validate_flow_events(ev)


def test_asof_never_uses_future_event():
    bars = pd.DatetimeIndex(
        [pd.Timestamp("2020-01-01 12:00", tz="UTC")], name="timestamp"
    )
    ev = pd.DataFrame(
        {
            "flow_time": pd.to_datetime(
                ["2020-01-01 08:00", "2020-01-01 16:00"], utc=True
            ),
            "net_flow": [-100.0, 500.0],
        }
    )
    asof = asof_flow_at_bar_close(bars, ev)
    assert float(asof["flow_last"].iloc[0]) == pytest.approx(-100.0)


def test_add_flow_features_no_lookahead():
    ohlcv = MockOHLCVSource(n=400, seed=2).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + pd.Timedelta(days=1)).date())
    ev = generate_mock_flow_events(start=start, end=end, seed=3)
    out = add_flow_features(ohlcv, ev)
    for col in (
        "flow_last",
        "flow_z_60",
        "flow_high",
        "flow_inflow_extreme",
        "flow_outflow_extreme",
    ):
        assert col in out.columns
    assert_flow_no_lookahead(out, ev, sample=80)


def test_feature_store_flow_cache(tmp_path: Path):
    from crl.shared.data.feature_store import (
        FEATURE_SCHEMA_VERSION_FLOW,
        load_or_build_features,
    )

    ohlcv = MockOHLCVSource(n=250, seed=0).fetch_ohlcv("BTCUSDT", "1d")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + pd.Timedelta(days=1)).date())
    ev = generate_mock_flow_events(start=start, end=end, seed=9)
    feat = load_or_build_features(
        ohlcv,
        dataset_id="mock_flow",
        cache_dir=tmp_path,
        force=True,
        flow_events=ev,
        flow_series_id="mock9",
    )
    assert "flow_last" in feat.columns
    assert any(FEATURE_SCHEMA_VERSION_FLOW in p.name for p in tmp_path.glob("*.parquet"))


def test_pre_registered_flow_hyps_count():
    import yaml

    d = Path("examples/batch/flow")
    if not d.exists():
        pytest.skip("flow programme not materialised")
    files = sorted(d.glob("hyp_flow_*.yaml"))
    assert len(files) == 8
    for f in files:
        raw = yaml.safe_load(f.read_text())
        assert "flow" in raw.get("feature_tags", []) or "flow_pit" in str(
            raw.get("feature_tags")
        )


def test_real_flow_ingest_fail_closed(tmp_path: Path):
    from crl.shared.data.sources.flow_ingest import load_flow_events, resolve_flow_series

    with pytest.raises(FlowPITError, match="not found"):
        load_flow_events(tmp_path / "nope.parquet")
    with pytest.raises(FlowPITError, match="No real flow"):
        resolve_flow_series("does_not_exist", flow_dir=tmp_path)


def test_load_real_flow_parquet(tmp_path: Path):
    from crl.shared.data.sources.flow_ingest import load_flow_events, resolve_flow_series

    ev = generate_mock_flow_events(start="2020-01-01", end="2020-02-01", seed=1)
    path = tmp_path / "demo.parquet"
    ev.to_parquet(path, index=False)
    loaded = load_flow_events(path)
    assert len(loaded) == len(ev)
    events, h = resolve_flow_series("demo", flow_dir=tmp_path)
    assert len(h) == 64
    assert len(events) == len(ev)


def test_cmd_netflow_publish_lag_no_same_day():
    from crl.shared.data.sources.flow_cmd_github import cmd_json_to_flow_events

    payload = {
        "data": [
            {"timestamp": 1_670_025_600_000, "value": -100.0, "last_modified": 1_800_000_000_000},
        ]
    }
    ev = cmd_json_to_flow_events(payload, publish_lag_days=1)
    assert len(ev) == 1
    # obs day 2022-12-03 → end day + 1d lag
    ft = ev["flow_time"].iloc[0]
    assert ft.day >= 4  # lag pushes past obs day
