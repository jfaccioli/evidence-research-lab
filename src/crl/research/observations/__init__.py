"""Deprecated import path — prefer crl.research.market_properties."""

from crl.research.market_properties.kline_aggression import (
    OBSERVATION_FAMILY_ID,
    PROPERTY_ID,
    build_aggression_frame,
    characterize_kline_aggression,
)

__all__ = [
    "OBSERVATION_FAMILY_ID",
    "PROPERTY_ID",
    "build_aggression_frame",
    "characterize_kline_aggression",
]
