"""Tiny-live risk envelope — enforced before any future LIVE adapter.

Pure functions; no exchange I/O. Used by paper/shadow/live when wired.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskEnvelope:
    """AUD-scale personal mandate defaults."""

    max_notional_aud: float = 50.0
    max_trades_per_day: int = 1
    max_position: float = 1.0  # full flat or full long (unit account)
    allow_short: bool = False
    max_leverage: float = 1.0
    kill_switch: bool = False  # human/ops latch


@dataclass
class RiskDecision:
    allowed: bool
    reason: str
    clipped_qty: float = 0.0


def check_order(
    *,
    side: str,
    qty: float,
    mark_price: float,
    trades_today: int,
    current_position: float,
    envelope: RiskEnvelope,
    fx_aud_per_usdt: float = 1.0,
) -> RiskDecision:
    """Fail closed on kill switch, trade count, short, leverage, notional."""
    if envelope.kill_switch:
        return RiskDecision(False, "kill_switch engaged", 0.0)
    if envelope.max_leverage > 1.0 + 1e-12:
        return RiskDecision(False, "leverage>1 not allowed in mandate", 0.0)
    if qty <= 0 or mark_price <= 0 or fx_aud_per_usdt <= 0:
        return RiskDecision(False, "invalid qty/price/fx", 0.0)
    if trades_today >= envelope.max_trades_per_day:
        return RiskDecision(
            False, f"max_trades_per_day={envelope.max_trades_per_day}", 0.0
        )

    side_l = side.lower()
    if side_l not in ("buy", "sell"):
        return RiskDecision(False, f"bad side {side}", 0.0)

    # Clip to max notional (AUD)
    max_qty = envelope.max_notional_aud / (mark_price * fx_aud_per_usdt)
    qty = min(float(qty), max_qty)

    if side_l == "buy":
        new_pos = current_position + qty
        if new_pos > envelope.max_position + 1e-9:
            qty = max(envelope.max_position - current_position, 0.0)
            new_pos = current_position + qty
    else:
        # sell
        if current_position <= 1e-12 and not envelope.allow_short:
            return RiskDecision(False, "shorting disabled (flat)", 0.0)
        if not envelope.allow_short:
            qty = min(qty, current_position)
        new_pos = current_position - qty
        if new_pos < -1e-12 and not envelope.allow_short:
            return RiskDecision(False, "shorting disabled", 0.0)

    if qty <= 1e-16:
        return RiskDecision(False, "qty clipped to zero", 0.0)
    if abs(new_pos) > envelope.max_position + 1e-9:
        return RiskDecision(False, "max_position exceeded", 0.0)

    return RiskDecision(True, "ok", float(qty))
