"""Mechanism-first studies (not trading programmes)."""

from __future__ import annotations

from crl.research.mechanisms.registry import load_registry, ranked_mechanisms
from crl.research.mechanisms.vol_clustering import MECHANISM_ID, study_vol_clustering
from crl.shared.data.sources.mock import MockOHLCVSource


def test_registry_loads():
    reg = load_registry()
    assert reg.get("version", 0) >= 1
    mechs = ranked_mechanisms()
    assert mechs[0]["id"] == "vol_clustering"


def test_vol_clustering_study_mock():
    ohlcv = MockOHLCVSource(n=400, seed=12).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    rep = study_vol_clustering(ohlcv, min_periods=40)
    assert rep["ok"] is True
    assert rep["mechanism_id"] == MECHANISM_ID
    assert rep["leda_candidate"] is False
    assert rep["p_high_rv_next_given_high_rv_lag"] is not None
