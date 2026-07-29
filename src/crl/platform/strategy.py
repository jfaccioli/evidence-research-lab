"""Strategy plug-in interface for the trading platform.

Strategies emit a *desired* target weight series in [0, 1] (long-only unit
mandate default). Execution lag and risk are applied outside the strategy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd


@dataclass(frozen=True)
class StrategyMeta:
    """Metadata — benchmarks are engineering artefacts only."""

    id: str
    name: str
    version: int = 1
    is_benchmark: bool = True
    is_scientific_candidate: bool = False
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.is_scientific_candidate and self.is_benchmark:
            raise ValueError("a strategy cannot be both scientific candidate and benchmark")


class Strategy(ABC):
    """Plug-in contract: pure signal generation from OHLCV (+ optional context)."""

    @property
    @abstractmethod
    def meta(self) -> StrategyMeta:
        ...

    @abstractmethod
    def desired_position(
        self,
        ohlcv: pd.DataFrame,
        *,
        context: dict[str, Any] | None = None,
    ) -> pd.Series:
        """Return target weight per bar index, values in [0, 1], long-only.

        Must use only information available at bar close (no look-ahead).
        Platform applies lag-1 fill at next open (research standard).
        """
        ...


_REGISTRY: dict[str, Callable[[], Strategy]] = {}


def register_strategy(factory: Callable[[], Strategy]) -> Callable[[], Strategy]:
    """Decorator / registrar for strategy factories."""
    inst = factory()
    sid = inst.meta.id
    if sid in _REGISTRY:
        raise ValueError(f"duplicate strategy id {sid}")
    _REGISTRY[sid] = factory
    return factory


def get_strategy(strategy_id: str) -> Strategy:
    if strategy_id not in _REGISTRY:
        raise KeyError(
            f"unknown strategy {strategy_id!r}; known={sorted(_REGISTRY)}"
        )
    return _REGISTRY[strategy_id]()


def list_strategies(*, benchmarks_only: bool = False) -> list[StrategyMeta]:
    out = []
    for fac in _REGISTRY.values():
        m = fac().meta
        if benchmarks_only and not m.is_benchmark:
            continue
        out.append(m)
    return sorted(out, key=lambda m: m.id)


def assert_not_live_eligible_unless_scientific(meta: StrategyMeta) -> None:
    """Benchmarks must never be treated as science-promoted production alpha."""
    if meta.is_benchmark:
        return
    if not meta.is_scientific_candidate:
        raise RuntimeError(f"{meta.id} not marked scientific candidate")
