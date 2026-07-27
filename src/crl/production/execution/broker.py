"""Broker interfaces for paper / shadow / live.

LIVE never places orders unless Phase-5 dual flags are set; even then
``LiveBroker`` remains a stub until exchange credentials and human review.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from crl.production.modes import ExecutionMode, assert_mode_allowed, live_explicitly_enabled
from crl.risk.constraints import RiskLimits, clamp_position


@dataclass
class OrderIntent:
    symbol: str
    side: str  # buy | sell
    qty: float
    intent_ts: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    client_tag: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class FillRecord:
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    ts: str
    mode: str
    simulated: bool = True


class Broker(ABC):
    mode: ExecutionMode

    @abstractmethod
    def place_order(self, order: OrderIntent, *, mark_price: float) -> FillRecord:
        ...

    @abstractmethod
    def position(self) -> float:
        ...


class PaperBroker(Broker):
    """Simulated fills at mark; tracks cash/position for paper mode."""

    mode = ExecutionMode.PAPER

    def __init__(
        self,
        *,
        limits: RiskLimits | None = None,
        fee_bps_rt: float = 33.0,
        starting_cash: float = 50.0,
    ) -> None:
        self.limits = limits or RiskLimits()
        self.fee_bps_rt = float(fee_bps_rt)
        self.cash = float(starting_cash)
        self._position = 0.0
        self.fills: list[FillRecord] = []

    def position(self) -> float:
        return self._position

    def place_order(self, order: OrderIntent, *, mark_price: float) -> FillRecord:
        assert_mode_allowed(ExecutionMode.PAPER)
        if order.symbol.upper().replace("/", "") not in ("BTCUSDT", "BTC/USDT"):
            raise ValueError("Paper broker Phase path: BTC only")
        side = order.side.lower()
        if side not in ("buy", "sell"):
            raise ValueError(side)
        qty = abs(float(order.qty))
        px = float(mark_price)
        if px <= 0 or qty <= 0:
            raise ValueError("invalid price/qty")
        target = self._position + qty if side == "buy" else self._position - qty
        target = clamp_position(target, self.limits)
        delta = target - self._position
        if abs(delta) < 1e-12:
            # no-op fill
            return FillRecord(
                symbol=order.symbol,
                side=side,
                qty=0.0,
                price=px,
                fee=0.0,
                ts=datetime.now(timezone.utc).isoformat(),
                mode=self.mode.value,
                simulated=True,
            )
        notional = abs(delta) * px
        fee = notional * (self.fee_bps_rt / 10_000.0)
        if delta > 0:
            self.cash -= notional + fee
        else:
            self.cash += notional - fee
        self._position = target
        fill = FillRecord(
            symbol=order.symbol,
            side="buy" if delta > 0 else "sell",
            qty=abs(delta),
            price=px,
            fee=fee,
            ts=datetime.now(timezone.utc).isoformat(),
            mode=self.mode.value,
            simulated=True,
        )
        self.fills.append(fill)
        return fill


class ShadowBroker(Broker):
    """Records would-be orders; never moves capital or hits an exchange."""

    mode = ExecutionMode.SHADOW

    def __init__(self) -> None:
        self.intents: list[OrderIntent] = []
        self._position = 0.0  # desired theoretical position only

    def position(self) -> float:
        return self._position

    def place_order(self, order: OrderIntent, *, mark_price: float) -> FillRecord:
        assert_mode_allowed(ExecutionMode.SHADOW)
        self.intents.append(order)
        # Theoretical full-or-flat mapping from last intent
        if order.side.lower() == "buy":
            self._position = 1.0
        else:
            self._position = 0.0
        return FillRecord(
            symbol=order.symbol,
            side=order.side,
            qty=float(order.qty),
            price=float(mark_price),
            fee=0.0,
            ts=datetime.now(timezone.utc).isoformat(),
            mode=self.mode.value,
            simulated=True,
        )


class LiveBroker(Broker):
    """Real orders — permanently stubbed until Phase 5 + exchange adapter."""

    mode = ExecutionMode.LIVE

    def __init__(self, *, config: dict | None = None) -> None:
        self.config = config or {}

    def position(self) -> float:
        raise RuntimeError("LiveBroker position query not implemented")

    def place_order(self, order: OrderIntent, *, mark_price: float) -> FillRecord:
        assert_mode_allowed(ExecutionMode.LIVE, config=self.config)
        # Even with flags, no exchange adapter is wired — fail closed.
        raise RuntimeError(
            "LiveBroker has no exchange adapter. Phase-5 requires a reviewed "
            "venue client, API keys (human), and independent safety review. "
            f"order={order!r} mark={mark_price} flags_ok={live_explicitly_enabled(config=self.config)}"
        )


def make_broker(mode: ExecutionMode, *, config: dict | None = None) -> Broker:
    assert_mode_allowed(mode, config=config)
    if mode == ExecutionMode.PAPER:
        return PaperBroker()
    if mode == ExecutionMode.SHADOW:
        return ShadowBroker()
    if mode == ExecutionMode.LIVE:
        return LiveBroker(config=config)
    raise ValueError(f"No broker for mode {mode}")
