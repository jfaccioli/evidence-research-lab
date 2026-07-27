"""Execution layer — paper/shadow scaffold; live hard-disabled by default.

Any production path must:
- refuse LIVE unless Phase-5 dual flags are set (see production.modes)
- enforce risk.constraints with no agent override path
- use only strategies in production.strategies.APPROVED (when populated)
"""

from __future__ import annotations

from crl.production.execution.broker import (
    Broker,
    FillRecord,
    LiveBroker,
    OrderIntent,
    PaperBroker,
    ShadowBroker,
    make_broker,
)
from crl.production.modes import ExecutionMode, assert_mode_allowed, live_explicitly_enabled


def place_order(*_args, **_kwargs):  # noqa: ANN001
    """Legacy hard stop — prefer make_broker(...).place_order."""
    raise RuntimeError(
        "Bare place_order is disabled. Use production.execution.make_broker "
        "with an allowed ExecutionMode. LIVE requires Phase-5 dual human flags "
        "and a reviewed exchange adapter (not implemented)."
    )


__all__ = [
    "Broker",
    "ExecutionMode",
    "FillRecord",
    "LiveBroker",
    "OrderIntent",
    "PaperBroker",
    "ShadowBroker",
    "assert_mode_allowed",
    "live_explicitly_enabled",
    "make_broker",
    "place_order",
]
