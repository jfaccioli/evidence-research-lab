"""Spot universe allow-list (BTC + ETH by default)."""

from __future__ import annotations

import pytest

from crl.risk.constraints import assert_phase1_universe
from crl.shared.universe import (
    asset_to_binance_symbol,
    allowed_spot_assets,
    is_asset_allowed,
    normalize_asset,
)
from crl.production.execution.broker import OrderIntent, PaperBroker


def test_normalize_and_binance_symbol():
    assert normalize_asset("ethusdt") == "ETH/USDT"
    assert normalize_asset("ETH/USDT") == "ETH/USDT"
    assert asset_to_binance_symbol("ETH/USDT") == "ETHUSDT"


def test_default_allows_btc_and_eth():
    a = allowed_spot_assets()
    assert "BTC/USDT" in a and "ETH/USDT" in a
    assert is_asset_allowed("ETHUSDT")
    assert not is_asset_allowed("DOGE/USDT")


def test_assert_universe_accepts_eth():
    assert_phase1_universe(
        {"asset": "ETH/USDT", "direction": "long_only", "leverage": 1}
    )


def test_assert_universe_rejects_doge():
    with pytest.raises(ValueError, match="not in spot universe"):
        assert_phase1_universe(
            {"asset": "DOGE/USDT", "direction": "long_only", "leverage": 1}
        )


def test_paper_broker_allows_eth():
    b = PaperBroker(starting_cash=100.0, fee_bps_rt=10.0)
    fill = b.place_order(
        OrderIntent(symbol="ETHUSDT", side="buy", qty=0.01),
        mark_price=3000.0,
    )
    assert fill.simulated
    assert b.position() > 0


def test_paper_broker_rejects_outside_universe():
    b = PaperBroker(starting_cash=100.0)
    with pytest.raises(ValueError, match="not in universe"):
        b.place_order(
            OrderIntent(symbol="DOGEUSDT", side="buy", qty=1.0),
            mark_price=0.1,
        )


def test_cfg_override_universe():
    cfg = {"universe": {"spot_assets": ["BTC/USDT"]}}
    assert is_asset_allowed("BTC/USDT", cfg)
    assert not is_asset_allowed("ETH/USDT", cfg)
    with pytest.raises(ValueError, match="not in spot universe"):
        assert_phase1_universe(
            {"asset": "ETH/USDT", "direction": "long_only"}, cfg=cfg
        )
