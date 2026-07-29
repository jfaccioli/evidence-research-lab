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

__all__ = [
    "KLINE_AGGRESSION_ID",
    "PERP_PREMIUM_ID",
    "characterize_kline_aggression",
    "characterize_perp_premium",
    "characterize_premium_residual",
]
