"""Execution mode ladder — research → paper → shadow → live.

LIVE order placement is hard-disabled until Phase 5 is explicitly opened
by a human (env + config flags). Scaffolding may exist earlier so the
path to automated trading is real, not improvised under capital risk.
"""

from __future__ import annotations

import os
from enum import Enum


class ExecutionMode(str, Enum):
    """Where capital risk begins."""

    RESEARCH = "research"  # offline backtests only
    PAPER = "paper"  # clock/sim fills, no exchange
    SHADOW = "shadow"  # live data/signals, no orders
    LIVE = "live"  # real orders — gated


# Human-operated gates (both required for LIVE).
LIVE_ENV_FLAG = "CRL_PHASE5_LIVE_ENABLED"
LIVE_CONFIG_FLAG = "phase5_live_enabled"


def live_explicitly_enabled(*, config: dict | None = None) -> bool:
    """True only if env and config both consent. Default False."""
    env_ok = os.environ.get(LIVE_ENV_FLAG, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    cfg = config or {}
    cfg_ok = bool(cfg.get(LIVE_CONFIG_FLAG, False)) or bool(
        (cfg.get("production") or {}).get(LIVE_CONFIG_FLAG, False)
    )
    return env_ok and cfg_ok


def assert_mode_allowed(mode: ExecutionMode, *, config: dict | None = None) -> None:
    """Fail closed: LIVE requires dual human flags; others always allowed as code paths."""
    if mode == ExecutionMode.LIVE and not live_explicitly_enabled(config=config):
        raise RuntimeError(
            "LIVE execution is disabled. Requires human Phase-5 open: "
            f"env {LIVE_ENV_FLAG}=true AND config {LIVE_CONFIG_FLAG}: true, "
            "after promotion ladder paper+shadow evidence."
        )
