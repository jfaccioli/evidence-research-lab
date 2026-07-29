"""LEDA-3: thin full-stack decision path (Forecast + Risk → Portfolio → Execution).

Not a promotion gate. Reuses existing layer stubs and RiskEnvelope.
Does not place live orders. Mode is recorded as intent only.
"""

from __future__ import annotations

from typing import Any

from crl.leda.layers import (
    execution_intent,
    forecast_passthrough,
    portfolio_long_only_unit,
    risk_from_vol_score,
)
from crl.leda.types import LayerName, LayerOutput
from crl.leda.util import payload_hash
from crl.production.risk_envelope import RiskEnvelope


def decide_bar(
    *,
    asof_time: str,
    e_forecast: float | None,
    e_risk: float | None,
    forecast_long_threshold: float = 0.5,
    risk_veto_threshold: float = 0.85,
    mode: str = "paper",
    envelope: RiskEnvelope | None = None,
) -> dict[str, Any]:
    """One-bar LEDA decision: map evidence scores → target position intent.

    Parameters
    ----------
    e_forecast
        Forecast-channel score in [0,1] (higher = more long support). None → flat intent.
    e_risk
        Risk-channel score in [0,1] (higher = more risk-off). None → no veto.
    """
    if e_forecast is not None and not (0.0 <= e_forecast <= 1.0):
        raise ValueError("e_forecast must be in [0,1] or None")
    if e_risk is not None and not (0.0 <= e_risk <= 1.0):
        raise ValueError("e_risk must be in [0,1] or None")

    inputs_hash = payload_hash(
        {
            "asof_time": asof_time,
            "e_forecast": e_forecast,
            "e_risk": e_risk,
            "forecast_long_threshold": forecast_long_threshold,
            "risk_veto_threshold": risk_veto_threshold,
            "mode": mode,
        }
    )

    want_long = bool(e_forecast is not None and e_forecast >= forecast_long_threshold)
    p_hat = float(e_forecast) if e_forecast is not None else None

    f_out = forecast_passthrough(
        asof_time=asof_time,
        p_hat=p_hat,
        evidence_scores={"e_forecast": e_forecast} if e_forecast is not None else {},
        inputs_hash=inputs_hash,
    )

    if e_risk is None:
        risk_veto = False
        r_out = LayerOutput(
            layer=LayerName.RISK,
            asof_time=asof_time,
            payload={
                "e_risk": None,
                "veto": False,
                "veto_threshold": risk_veto_threshold,
                "meaning": "no risk evidence supplied",
                "decides_size": False,
            },
            inputs_hash=inputs_hash,
        )
    else:
        r_out = risk_from_vol_score(
            asof_time=asof_time,
            e_risk=e_risk,
            veto_threshold=risk_veto_threshold,
            inputs_hash=inputs_hash,
        )
        risk_veto = bool(r_out.payload["veto"])

    p_out = portfolio_long_only_unit(
        asof_time=asof_time,
        want_long=want_long,
        risk_veto=risk_veto,
        envelope=envelope,
        inputs_hash=inputs_hash,
    )
    x_out = execution_intent(
        asof_time=asof_time,
        target_position=float(p_out.payload["target_position"]),
        mode=mode,
        inputs_hash=inputs_hash,
    )

    return {
        "asof_time": asof_time,
        "inputs_hash": inputs_hash,
        "want_long": want_long,
        "risk_veto": risk_veto,
        "target_position": float(p_out.payload["target_position"]),
        "layers": {
            "forecast": f_out.to_dict(),
            "risk": r_out.to_dict(),
            "portfolio": p_out.to_dict(),
            "execution": x_out.to_dict(),
        },
        "promotion": "not_applicable — stack wire only; frozen economic gates separate",
    }
