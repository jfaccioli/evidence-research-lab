"""Production surface — paper/shadow scaffolding; LIVE fail-closed.

Research may explore freely under frozen gates. Production stays boring:
only APPROVED strategies may later be clocked; bare place_order stays disabled;
LIVE needs Phase-5 dual human flags + exchange adapter (not implemented).
"""

from crl.production.modes import ExecutionMode, live_explicitly_enabled

PHASE1_EXECUTION_ENABLED = False  # legacy name; LIVE still dual-flag gated

__all__ = [
    "ExecutionMode",
    "PHASE1_EXECUTION_ENABLED",
    "live_explicitly_enabled",
]
