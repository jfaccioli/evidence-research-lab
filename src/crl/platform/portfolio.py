"""Thin portfolio construction — single-strategy long-only by default."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PortfolioConfig:
    """Until multi-strategy science exists, only one sleeve is active."""

    max_gross: float = 1.0
    long_only: bool = True


def combine_single(desired: pd.Series, cfg: PortfolioConfig | None = None) -> pd.Series:
    """Pass-through for one strategy under gross cap."""
    cfg = cfg or PortfolioConfig()
    d = desired.astype(float)
    if cfg.long_only:
        d = d.clip(0.0, None)
    return d.clip(upper=cfg.max_gross).rename("portfolio_target")


def combine_equal_weight(
    desired_map: dict[str, pd.Series],
    cfg: PortfolioConfig | None = None,
) -> pd.Series:
    """Equal-weight average of multiple desired series (future multi-strategy)."""
    cfg = cfg or PortfolioConfig()
    if not desired_map:
        raise ValueError("empty desired_map")
    aligned = pd.concat(desired_map.values(), axis=1).astype(float)
    avg = aligned.mean(axis=1)
    if cfg.long_only:
        avg = avg.clip(0.0, None)
    return avg.clip(upper=cfg.max_gross).rename("portfolio_target")
