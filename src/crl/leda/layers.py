"""Thin LEDA layer stubs — contracts only until more channels exist.

Portfolio/Execution reuse existing production modules; no new optimizers.
"""

from __future__ import annotations

from typing import Any, Optional

from crl.leda.types import LayerName, LayerOutput
from crl.production.risk_envelope import RiskEnvelope


def forecast_passthrough(
    *,
    asof_time: str,
    p_hat: float | None,
    evidence_scores: dict[str, float],
    inputs_hash: str,
) -> LayerOutput:
    """Forecast layer: assemble predictive scores; no sizing."""
    return LayerOutput(
        layer=LayerName.FORECAST,
        asof_time=asof_time,
        payload={
            "p_hat": p_hat,
            "evidence": evidence_scores,
            "decides_trade": False,
        },
        inputs_hash=inputs_hash,
    )


def risk_from_vol_score(
    *,
    asof_time: str,
    e_risk: float,
    veto_threshold: float = 0.85,
    inputs_hash: str,
) -> LayerOutput:
    """Risk layer: map vol-risk evidence to veto (thin default)."""
    if not (0.0 <= e_risk <= 1.0):
        raise ValueError("e_risk must be in [0,1]")
    if not (0.0 < veto_threshold <= 1.0):
        raise ValueError("invalid veto_threshold")
    veto = bool(e_risk >= veto_threshold)
    return LayerOutput(
        layer=LayerName.RISK,
        asof_time=asof_time,
        payload={
            "e_risk": e_risk,
            "veto": veto,
            "veto_threshold": veto_threshold,
            "meaning": "high e_risk = risk-off pressure",
            "decides_size": False,
        },
        inputs_hash=inputs_hash,
    )


def portfolio_long_only_unit(
    *,
    asof_time: str,
    want_long: bool,
    risk_veto: bool,
    envelope: RiskEnvelope | None = None,
    inputs_hash: str,
) -> LayerOutput:
    """Portfolio layer: 0/1 long-only; veto forces flat. No multi-asset optim."""
    env = envelope or RiskEnvelope()
    if env.max_leverage > 1.0 + 1e-12:
        raise ValueError("leverage>1 forbidden in LEDA portfolio default")
    target = 0.0
    if want_long and not risk_veto:
        target = min(1.0, float(env.max_position))
    return LayerOutput(
        layer=LayerName.PORTFOLIO,
        asof_time=asof_time,
        payload={
            "target_position": target,
            "want_long": want_long,
            "risk_veto": risk_veto,
            "max_position": env.max_position,
        },
        inputs_hash=inputs_hash,
    )


def execution_intent(
    *,
    asof_time: str,
    target_position: float,
    mode: str,
    inputs_hash: str,
) -> LayerOutput:
    """Execution layer: record intent only; LIVE still dual-flag elsewhere."""
    return LayerOutput(
        layer=LayerName.EXECUTION,
        asof_time=asof_time,
        payload={
            "target_position": target_position,
            "mode": mode,
            "fill": "next_open",
            "places_live_orders": False,
        },
        inputs_hash=inputs_hash,
    )
