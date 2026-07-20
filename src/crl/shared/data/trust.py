"""Rule-based data trust scores (not ML)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrustFactors:
    source_class: str
    completeness: float = 1.0
    timestamp_monotonic: float = 1.0
    ohlc_consistency: float = 1.0
    history_depth_years: float = 0.0


# Base trust by source class (plan § data quality)
SOURCE_BASE: dict[str, float] = {
    "exchange_native": 0.97,
    "binance_public": 0.97,
    "aggregator": 0.85,
    "index": 0.78,
    "social_reconstructed": 0.55,
    "unverified_scrape": 0.30,
    "mock": 0.50,
}


def score_trust(factors: TrustFactors) -> float:
    base = SOURCE_BASE.get(factors.source_class, 0.40)
    depth_bonus = min(0.02, max(0.0, factors.history_depth_years / 50.0))
    raw = (
        base
        * factors.completeness
        * factors.timestamp_monotonic
        * factors.ohlc_consistency
        + depth_bonus
    )
    return float(max(0.0, min(1.0, raw)))
