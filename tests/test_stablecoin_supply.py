"""Aggregate stablecoin supply market property."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.market_properties.stablecoin_supply import (
    PROPERTY_ID,
    characterize_stablecoin_supply,
)
from crl.shared.data.stablecoin_supply import supply_events_hash, validate_supply_events
from crl.shared.data.sources.mock import MockOHLCVSource


def test_characterize_stable_supply_mock():
    ohlcv = MockOHLCVSource(n=400, seed=8).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    rng = np.random.default_rng(3)
    level = 1e10 * np.exp(np.cumsum(rng.normal(0.0003, 0.003, size=len(ohlcv))))
    supply = pd.DataFrame({"event_time": ohlcv.index, "supply_usd": level})
    v = validate_supply_events(supply)
    assert len(supply_events_hash(v)) == 64
    rep = characterize_stablecoin_supply(ohlcv, supply, min_points=50)
    assert rep["ok"] is True
    assert rep["property_id"] == PROPERTY_ID
    assert rep["leda_candidate"] is False
    assert "independence_vs_known_properties" in rep
