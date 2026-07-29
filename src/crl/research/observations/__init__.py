"""Market observation discovery — characterize measurable properties first.

Not a signal factory. See docs/OBSERVATION_DISCOVERY_DIRECTIVE.md.
"""

from crl.research.observations.kline_aggression import (
    OBSERVATION_FAMILY_ID,
    build_aggression_frame,
    characterize_kline_aggression,
)

__all__ = [
    "OBSERVATION_FAMILY_ID",
    "build_aggression_frame",
    "characterize_kline_aggression",
]
