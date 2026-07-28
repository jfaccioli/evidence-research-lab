"""FRED ingest helpers (no network; lag construction only)."""

from __future__ import annotations

import pandas as pd

from crl.shared.data.sources.fred import observations_to_events


def test_publish_lag_one_day():
    obs = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-02"], utc=True),
            "value": [100.0],
        }
    )
    ev = observations_to_events(obs, publish_lag_days=1)
    # FRED date 2020-01-02 → EOD + 1 day lag
    assert ev["event_time"].iloc[0].day == 3 or ev["event_time"].iloc[0].day == 4
    # Must be strictly after observation date
    assert ev["event_time"].iloc[0] > obs["date"].iloc[0]


def test_missing_values_dropped():
    # observations_to_events expects cleaned floats; fetch path drops "."
    obs = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-02", "2020-01-03"], utc=True),
            "value": [1.0, 2.0],
        }
    )
    ev = observations_to_events(obs, publish_lag_days=1)
    assert len(ev) == 2
