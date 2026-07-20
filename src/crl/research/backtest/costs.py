"""Transaction cost model."""

from __future__ import annotations

from crl.shared.types import CostConfig


def one_way_cost_fraction(cfg: CostConfig, stress: bool = False) -> float:
    return cfg.total_bps_one_way(stress=stress) / 10_000.0


def apply_buy_price(open_price: float, cfg: CostConfig, stress: bool = False) -> float:
    """Pay more on entry (long)."""
    return open_price * (1.0 + one_way_cost_fraction(cfg, stress=stress))


def apply_sell_price(open_price: float, cfg: CostConfig, stress: bool = False) -> float:
    """Receive less on exit (long)."""
    return open_price * (1.0 - one_way_cost_fraction(cfg, stress=stress))
