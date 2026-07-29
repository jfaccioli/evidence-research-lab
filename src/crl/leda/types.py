"""LEDA-0: thin contracts for evidence and layers.

Keep deliberately small — only what is needed for scientific reproducibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class LayerName(str, Enum):
    FORECAST = "forecast"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    EXECUTION = "execution"


class EvidenceSink(str, Enum):
    """Which decision layer consumes this evidence primarily."""

    FORECAST = "forecast"
    RISK = "risk"
    BOTH = "both"


@dataclass(frozen=True)
class EvidenceRecord:
    """One PIT evidence point from a channel.

    ``score`` is on a fixed scale for the channel (documented in channel design).
    For Risk channels, higher score = more risk-off / less trust in risk-on exposure.
    For Forecast channels, higher score = more support for risk-on (long) thesis
    unless the channel design says otherwise.
    """

    channel_id: str
    version: int
    sink: EvidenceSink
    asof_time: str  # ISO UTC
    score: float  # typically [0, 1]
    inputs_hash: str
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= float(self.score) <= 1.0):
            raise ValueError(f"score must be in [0,1], got {self.score}")
        if not self.channel_id:
            raise ValueError("channel_id required")
        if not self.inputs_hash:
            raise ValueError("inputs_hash required")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["sink"] = self.sink.value
        return d


@dataclass(frozen=True)
class LayerOutput:
    """Generic layer output for audit trails."""

    layer: LayerName
    asof_time: str
    payload: dict[str, Any]
    inputs_hash: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["layer"] = self.layer.value
        return d


# --- Layer contracts (documentation-as-code; enforced by review + tests) ---

LAYER_CONTRACTS: dict[LayerName, dict[str, Any]] = {
    LayerName.FORECAST: {
        "must": [
            "Emit predictive scores/probabilities for a pre-registered target",
            "Report uncertainty when available",
            "Use only PIT inputs (event_time <= bar close)",
        ],
        "must_not": [
            "Choose position size",
            "Place or simulate orders",
            "Silently apply risk vetoes",
        ],
    },
    LayerName.RISK: {
        "must": [
            "Emit risk-off pressure, veto, or trust scores from PIT risk features",
            "Declare what 'high score' means (risk-off vs risk-on)",
        ],
        "must_not": [
            "Override forecast labels",
            "Invent directional alpha under a risk name",
            "Set final notional beyond documenting a veto",
        ],
    },
    LayerName.PORTFOLIO: {
        "must": [
            "Map (forecast, risk) to target exposure under frozen constraints",
            "Respect mandate (long-only, max position, no leverage)",
        ],
        "must_not": [
            "Peek at confirmatory test when fitting maps",
            "Change economic thesis (that belongs in forecast/risk design)",
        ],
    },
    LayerName.EXECUTION: {
        "must": [
            "Realize portfolio targets under ExecutionMode",
            "Apply costs/kill-switch/LIVE dual flags",
        ],
        "must_not": [
            "Change forecast or risk science",
            "Enable LIVE without dual flags",
        ],
    },
}
