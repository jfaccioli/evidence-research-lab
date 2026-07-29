"""Perpetual premium market property characterization."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.market_properties.perp_premium import (
    PROPERTY_ID,
    characterize_perp_premium,
)
from crl.shared.data.premium import premium_events_hash, validate_premium_events
from crl.shared.data.sources.mock import MockOHLCVSource


def _mock_premium(ohlcv: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Mild persistence + correlation with returns for test structure
    rets = ohlcv["close"].pct_change().fillna(0).to_numpy()
    noise = rng.normal(0, 0.0002, size=len(ohlcv))
    prem = 0.0001 * np.cumsum(rets) * 0 + np.cumsum(noise) * 0.1
    prem = prem - np.mean(prem)
    return pd.DataFrame(
        {
            "event_time": ohlcv.index,
            "premium_close": prem,
            "premium_open": prem,
            "premium_high": prem + 1e-5,
            "premium_low": prem - 1e-5,
        }
    )


def test_validate_and_hash_premium():
    ohlcv = MockOHLCVSource(n=50, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    prem = _mock_premium(ohlcv)
    v = validate_premium_events(prem)
    h = premium_events_hash(v)
    assert len(h) == 64


def test_characterize_premium_mock():
    ohlcv = MockOHLCVSource(n=400, seed=2).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    prem = _mock_premium(ohlcv, seed=3)
    # Synthetic funding
    fund = pd.DataFrame(
        {
            "funding_time": ohlcv.index[::3],
            "funding_rate": np.random.default_rng(4).normal(0, 1e-4, size=len(ohlcv[::3])),
        }
    )
    rep = characterize_perp_premium(ohlcv, prem, funding_events=fund, min_points=50)
    assert rep["ok"] is True
    assert rep["property_id"] == PROPERTY_ID
    assert rep["promotion"].startswith("not_applicable")
    assert rep["leda_candidate"] is False
    assert "independence_vs_known_properties" in rep
    assert "what_it_measures" in rep

    from crl.research.market_properties.perp_premium import characterize_premium_residual

    res = characterize_premium_residual(
        ohlcv, prem, fund, min_points=50, expand_min=40
    )
    assert res["ok"] is True
    assert res["property_id"] == "premium_residual_vs_funding"
    assert res["leda_candidate"] is False
