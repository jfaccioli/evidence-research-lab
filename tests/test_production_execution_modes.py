"""Paper/shadow allowed; live hard-disabled without dual flags."""

from __future__ import annotations

import pytest

from crl.production.execution import (
    LiveBroker,
    OrderIntent,
    PaperBroker,
    ShadowBroker,
    make_broker,
    place_order,
)
from crl.production.modes import ExecutionMode, assert_mode_allowed, live_explicitly_enabled


def test_bare_place_order_disabled():
    with pytest.raises(RuntimeError, match="disabled"):
        place_order("BTCUSDT", "buy", 1.0)


def test_paper_broker_sim_fill():
    b = PaperBroker(starting_cash=100.0, fee_bps_rt=10.0)
    fill = b.place_order(
        OrderIntent(symbol="BTCUSDT", side="buy", qty=0.001),
        mark_price=50_000.0,
    )
    assert fill.simulated
    assert b.position() > 0
    assert len(b.fills) == 1


def test_shadow_records_without_cash():
    b = ShadowBroker()
    b.place_order(
        OrderIntent(symbol="BTCUSDT", side="buy", qty=1.0),
        mark_price=50_000.0,
    )
    assert len(b.intents) == 1
    assert b.position() == 1.0


def test_live_blocked_without_flags(monkeypatch):
    monkeypatch.delenv("CRL_PHASE5_LIVE_ENABLED", raising=False)
    assert live_explicitly_enabled(config={}) is False
    with pytest.raises(RuntimeError, match="LIVE execution is disabled"):
        assert_mode_allowed(ExecutionMode.LIVE, config={})
    with pytest.raises(RuntimeError, match="LIVE execution is disabled"):
        make_broker(ExecutionMode.LIVE, config={})


def test_live_broker_stub_even_with_flags(monkeypatch):
    monkeypatch.setenv("CRL_PHASE5_LIVE_ENABLED", "true")
    cfg = {"phase5_live_enabled": True}
    assert live_explicitly_enabled(config=cfg) is True
    b = LiveBroker(config=cfg)
    with pytest.raises(RuntimeError, match="no exchange adapter"):
        b.place_order(
            OrderIntent(symbol="BTCUSDT", side="buy", qty=0.001),
            mark_price=50_000.0,
        )
