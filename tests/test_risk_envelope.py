from crl.production.risk_envelope import RiskEnvelope, check_order


def test_kill_switch_blocks():
    d = check_order(
        side="buy",
        qty=0.001,
        mark_price=50_000,
        trades_today=0,
        current_position=0.0,
        envelope=RiskEnvelope(kill_switch=True),
    )
    assert not d.allowed


def test_max_trades_per_day():
    d = check_order(
        side="buy",
        qty=0.001,
        mark_price=50_000,
        trades_today=1,
        current_position=0.0,
        envelope=RiskEnvelope(max_trades_per_day=1),
    )
    assert not d.allowed


def test_no_short_from_flat():
    d = check_order(
        side="sell",
        qty=0.001,
        mark_price=50_000,
        trades_today=0,
        current_position=0.0,
        envelope=RiskEnvelope(),
    )
    assert not d.allowed


def test_buy_clips_notional():
    env = RiskEnvelope(max_notional_aud=50.0)
    d = check_order(
        side="buy",
        qty=10.0,  # huge
        mark_price=50_000,
        trades_today=0,
        current_position=0.0,
        envelope=env,
    )
    assert d.allowed
    assert d.clipped_qty * 50_000 <= 50.0 + 1e-6
