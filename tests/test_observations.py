"""Observation discovery characterization (not trade gates)."""

from __future__ import annotations

import pytest

from crl.research.market_properties.kline_aggression import (
    PROPERTY_ID,
    build_aggression_frame,
    characterize_kline_aggression,
)
from crl.shared.data.sources.mock import MockOHLCVSource


def test_mock_has_microstructure_columns():
    df = MockOHLCVSource(n=100, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    assert "taker_buy_base" in df.columns
    assert "n_trades" in df.columns
    assert (df["taker_buy_base"] <= df["volume"] + 1e-9).all()


def test_characterize_aggression_mock():
    ohlcv = MockOHLCVSource(n=400, seed=5).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    frame = build_aggression_frame(ohlcv)
    assert "taker_buy_ratio_lag" in frame.columns
    rep = characterize_kline_aggression(ohlcv, min_points=50)
    assert rep["ok"] is True
    assert rep["property_id"] == PROPERTY_ID
    assert "independence_vs_known_properties" in rep
    assert "association_next_state" in rep
    assert "not_applicable" in rep["promotion"]
    assert rep.get("leda_candidate") is False


def test_missing_micro_fails_closed():
    ohlcv = MockOHLCVSource(n=100, seed=0).fetch_ohlcv("BTCUSDT", "1d")
    thin = ohlcv[["open", "high", "low", "close", "volume"]].copy()
    with pytest.raises(ValueError, match="missing columns"):
        build_aggression_frame(thin)
