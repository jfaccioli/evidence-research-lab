"""Market property discovery — characterize measurable market behaviour.

Not a signal factory. See docs/MARKET_PROPERTIES_DIRECTIVE.md.
"""

from crl.research.market_properties.kline_aggression import (
    PROPERTY_ID as KLINE_AGGRESSION_ID,
    characterize_kline_aggression,
)
from crl.research.market_properties.perp_premium import (
    PROPERTY_ID as PERP_PREMIUM_ID,
    characterize_perp_premium,
    characterize_premium_residual,
)
from crl.research.market_properties.stablecoin_supply import (
    PROPERTY_ID as STABLE_SUPPLY_ID,
    characterize_stablecoin_supply,
)
from crl.research.market_properties.cross_venue_basis import (
    PROPERTY_ID as CROSS_VENUE_ID,
    characterize_cross_venue_basis,
)
from crl.research.market_properties.synthesis import run_property_synthesis_review

__all__ = [
    "KLINE_AGGRESSION_ID",
    "PERP_PREMIUM_ID",
    "STABLE_SUPPLY_ID",
    "CROSS_VENUE_ID",
    "characterize_kline_aggression",
    "characterize_perp_premium",
    "characterize_premium_residual",
    "characterize_stablecoin_supply",
    "characterize_cross_venue_basis",
    "run_property_synthesis_review",
]
