"""Position sizing modules — platform engineering, not alpha."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SizingConfig:
    """Long-only unit mandate defaults."""

    mode: str = "full_or_flat"  # full_or_flat | fixed_fraction
    max_position: float = 1.0
    fixed_fraction: float = 1.0


def apply_sizing(desired: pd.Series, cfg: SizingConfig | None = None) -> pd.Series:
    """Map raw desired signal to target weight under sizing rules."""
    cfg = cfg or SizingConfig()
    d = desired.astype(float).clip(0.0, 1.0)
    if cfg.mode == "full_or_flat":
        out = (d >= 0.5).astype(float) * min(1.0, cfg.max_position)
    elif cfg.mode == "fixed_fraction":
        frac = min(max(cfg.fixed_fraction, 0.0), cfg.max_position)
        out = (d >= 0.5).astype(float) * frac
    else:
        raise ValueError(f"unknown sizing mode {cfg.mode}")
    return out.rename("sized")
