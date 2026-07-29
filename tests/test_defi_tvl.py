"""DeFi TVL market property characterization."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.market_properties.defi_tvl import PROPERTY_ID, characterize_defi_tvl
from crl.shared.data.sources.mock import MockOHLCVSource


def test_characterize_defi_tvl_mock():
    ohlcv = MockOHLCVSource(n=400, seed=4).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    rng = np.random.default_rng(5)
    level = 1e9 * np.exp(np.cumsum(rng.normal(0.001, 0.02, size=len(ohlcv))))
    tvl = pd.DataFrame({"event_time": ohlcv.index, "tvl_usd": level})
    rep = characterize_defi_tvl(ohlcv, tvl, min_points=50)
    assert rep["ok"] is True
    assert rep["property_id"] == PROPERTY_ID
    assert rep["leda_candidate"] is False
