from crl.research.backtest.costs import one_way_cost_fraction
from crl.shared.types import CostConfig


def test_one_way_cost():
    c = CostConfig(fee_bps_per_side=10, half_spread_bps=2, slippage_bps_per_side=5)
    assert abs(one_way_cost_fraction(c) - 17 / 10_000) < 1e-12


def test_stress_doubles():
    c = CostConfig(fee_bps_per_side=10, half_spread_bps=0, slippage_bps_per_side=0, stress_multiplier=2)
    assert abs(one_way_cost_fraction(c, stress=True) - 2 * one_way_cost_fraction(c)) < 1e-12
