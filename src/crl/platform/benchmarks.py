"""Deterministic benchmark strategies — engineering validation only.

Not scientific claims. Not trading recommendations. Not LIVE-eligible.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from crl.platform.strategy import Strategy, StrategyMeta, register_strategy


def _close(ohlcv: pd.DataFrame) -> pd.Series:
    if "close" not in ohlcv.columns:
        raise ValueError("ohlcv requires close")
    return ohlcv["close"].astype(float)


@register_strategy
def _buy_and_hold() -> Strategy:
    class BuyAndHold(Strategy):
        @property
        def meta(self) -> StrategyMeta:
            return StrategyMeta(
                id="bench_buy_and_hold",
                name="Buy & Hold",
                is_benchmark=True,
                description="Always fully long — engineering baseline",
            )

        def desired_position(
            self, ohlcv: pd.DataFrame, *, context: dict[str, Any] | None = None
        ) -> pd.Series:
            return pd.Series(1.0, index=ohlcv.index, name="desired")

    return BuyAndHold()


@register_strategy
def _sma_cross() -> Strategy:
    class SmaCross(Strategy):
        def __init__(self, fast: int = 50, slow: int = 200) -> None:
            self.fast = fast
            self.slow = slow

        @property
        def meta(self) -> StrategyMeta:
            return StrategyMeta(
                id="bench_sma_cross",
                name="SMA Cross",
                is_benchmark=True,
                description=f"Long when SMA{self.fast} > SMA{self.slow}",
                params={"fast": self.fast, "slow": self.slow},
            )

        def desired_position(
            self, ohlcv: pd.DataFrame, *, context: dict[str, Any] | None = None
        ) -> pd.Series:
            c = _close(ohlcv)
            f = c.rolling(self.fast, min_periods=self.fast).mean()
            s = c.rolling(self.slow, min_periods=self.slow).mean()
            # Causal: signal at t uses SMAs through t; lag applied by engine
            des = (f > s).astype(float)
            return des.rename("desired")

    return SmaCross()


@register_strategy
def _tsmom() -> Strategy:
    class TimeSeriesMomentum(Strategy):
        def __init__(self, lookback: int = 20) -> None:
            self.lookback = lookback

        @property
        def meta(self) -> StrategyMeta:
            return StrategyMeta(
                id="bench_tsmom",
                name="Time-Series Momentum",
                is_benchmark=True,
                description=f"Long when {self.lookback}d return > 0",
                params={"lookback": self.lookback},
            )

        def desired_position(
            self, ohlcv: pd.DataFrame, *, context: dict[str, Any] | None = None
        ) -> pd.Series:
            c = _close(ohlcv)
            ret = c / c.shift(self.lookback) - 1.0
            return (ret > 0).astype(float).rename("desired")

    return TimeSeriesMomentum()


@register_strategy
def _random_control() -> Strategy:
    class RandomControl(Strategy):
        def __init__(self, seed: int = 42, p_long: float = 0.5) -> None:
            self.seed = seed
            self.p_long = p_long

        @property
        def meta(self) -> StrategyMeta:
            return StrategyMeta(
                id="bench_random_control",
                name="Random Control",
                is_benchmark=True,
                description="Deterministic pseudo-random long/flat (fixed seed)",
                params={"seed": self.seed, "p_long": self.p_long},
            )

        def desired_position(
            self, ohlcv: pd.DataFrame, *, context: dict[str, Any] | None = None
        ) -> pd.Series:
            # Deterministic from seed + bar index position (not wall clock)
            rng = np.random.default_rng(self.seed)
            n = len(ohlcv)
            u = rng.random(n)
            des = (u < self.p_long).astype(float)
            return pd.Series(des, index=ohlcv.index, name="desired")

    return RandomControl()


def all_benchmark_ids() -> list[str]:
    return [
        "bench_buy_and_hold",
        "bench_sma_cross",
        "bench_tsmom",
        "bench_random_control",
    ]
