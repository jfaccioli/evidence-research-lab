"""Deterministic risk constraints — not overridable by agents.

Project policy: no leverage as trading vehicle (see docs/POLICY_NO_LEVERAGE.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Hard product mandate — do not raise above 1.0 without human policy change.
MAX_LEVERAGE_MANDATE = 1.0


@dataclass(frozen=True)
class RiskLimits:
    max_position: float = 1.0
    min_position: float = 0.0
    max_leverage: float = 1.0
    allow_short: bool = False
    allow_derivatives: bool = False


def clamp_position(pos: float, limits: RiskLimits) -> float:
    if not limits.allow_short and pos < 0:
        pos = 0.0
    pos = min(pos, limits.max_position)
    pos = max(pos, limits.min_position)
    if abs(pos) > limits.max_leverage:
        pos = limits.max_leverage if pos > 0 else -limits.max_leverage
    return float(pos)


def assert_phase1_universe(
    spec_dict: dict[str, Any],
    cfg: dict[str, Any] | None = None,
) -> None:
    """Hard reject assets/directions outside the spot mandate.

    Spot assets come from ``cfg['universe']['spot_assets']`` (default BTC+ETH).
    Long-only, no leverage, no derivatives remain hard policy.
    """
    from crl.shared.universe import allowed_spot_assets, normalize_asset

    asset = normalize_asset(str(spec_dict.get("asset", "")))
    direction = spec_dict.get("direction", "") or "long_only"
    allowed = allowed_spot_assets(cfg)
    if asset not in allowed:
        raise ValueError(
            f"Asset {spec_dict.get('asset')!r} not in spot universe "
            f"{sorted(allowed)} (docs/MULTI_ASSET_V1.md)"
        )
    if direction not in ("long_only", "long"):
        raise ValueError(f"long_only only, got {direction}")
    lev = spec_dict.get("leverage", 1)
    if lev not in (1, 1.0, None):
        raise ValueError("Leverage not allowed (project mandate: spot only, max_leverage=1)")
    if spec_dict.get("allow_derivatives") or spec_dict.get("vehicle") in (
        "perp",
        "futures",
        "margin",
    ):
        raise ValueError("Derivatives/margin vehicles not allowed under no-leverage mandate")


def risk_from_config(cfg: dict) -> RiskLimits:
    r = cfg.get("risk", {})
    max_lev = float(r.get("max_leverage", 1.0))
    if max_lev > MAX_LEVERAGE_MANDATE + 1e-12:
        raise ValueError(
            f"configs.risk.max_leverage={max_lev} violates mandate "
            f"MAX_LEVERAGE_MANDATE={MAX_LEVERAGE_MANDATE} (docs/POLICY_NO_LEVERAGE.md)"
        )
    return RiskLimits(
        max_position=float(r.get("max_position", 1.0)),
        min_position=float(r.get("min_position", 0.0)),
        max_leverage=max_lev,
        allow_short=bool(r.get("allow_short", False)),
        allow_derivatives=bool(r.get("allow_derivatives", False)),
    )
