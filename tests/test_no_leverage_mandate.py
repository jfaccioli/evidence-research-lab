import pytest

from crl.risk.constraints import assert_phase1_universe, risk_from_config


def test_config_rejects_leverage_above_one():
    with pytest.raises(ValueError, match="MAX_LEVERAGE_MANDATE"):
        risk_from_config({"risk": {"max_leverage": 2.0}})


def test_config_allows_unit_leverage():
    lim = risk_from_config({"risk": {"max_leverage": 1.0}})
    assert lim.max_leverage == 1.0


def test_spec_rejects_leverage():
    with pytest.raises(ValueError, match="Leverage not allowed"):
        assert_phase1_universe(
            {"asset": "BTC/USDT", "direction": "long_only", "leverage": 5}
        )


def test_spec_rejects_perp_vehicle():
    with pytest.raises(ValueError, match="Derivatives"):
        assert_phase1_universe(
            {
                "asset": "BTC/USDT",
                "direction": "long_only",
                "vehicle": "perp",
            }
        )
