"""Platform risk manager — exposure, leverage, daily loss, kill switch."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from crl.production.kill_switch import is_kill_switch_engaged
from crl.production.risk_envelope import RiskEnvelope


@dataclass(frozen=True)
class PlatformRiskConfig:
    max_position: float = 1.0
    max_leverage: float = 1.0
    max_daily_loss_frac: float = 0.10  # halt new risk if day equity drop exceeds
    respect_kill_switch: bool = True
    envelope: RiskEnvelope | None = None


def apply_risk_to_target(
    target: pd.Series,
    equity: pd.Series | None = None,
    *,
    cfg: PlatformRiskConfig | None = None,
) -> pd.Series:
    """Clip targets under risk rules (vectorised historical path).

    Daily loss: if equity drops more than max_daily_loss_frac from prior day
    peak of that calendar day, force flat for remainder of that day (approx:
    force flat on bars where trailing day return < -threshold).
    """
    cfg = cfg or PlatformRiskConfig()
    if cfg.max_leverage > 1.0 + 1e-12:
        raise ValueError("leverage>1 forbidden in platform default mandate")
    if cfg.respect_kill_switch and is_kill_switch_engaged():
        return pd.Series(0.0, index=target.index, name="risk_target")

    out = target.astype(float).clip(0.0, cfg.max_position)

    if equity is not None and len(equity) == len(target):
        # Bar-to-bar drawdown from expanding peak as crude daily-loss proxy
        peak = equity.cummax()
        dd = equity / peak - 1.0
        halt = dd < -abs(cfg.max_daily_loss_frac)
        out = out.where(~halt, 0.0)

    return out.rename("risk_target")
