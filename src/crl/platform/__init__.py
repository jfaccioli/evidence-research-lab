"""Trading Platform — production engineering (parallel to Alpha Discovery).

Benchmark strategies validate the machinery only. They are **not** scientific
claims and **not** eligible for LIVE until (and unless) a confirmatory survivor
is promoted through the existing science pathway.

See docs/TRADING_PLATFORM_V1.md.
"""

from crl.platform import benchmarks as _benchmarks  # noqa: F401 — register plug-ins
from crl.platform.engine import PlatformRunResult, run_platform_backtest
from crl.platform.strategy import Strategy, StrategyMeta, get_strategy, list_strategies

__all__ = [
    "Strategy",
    "StrategyMeta",
    "list_strategies",
    "get_strategy",
    "PlatformRunResult",
    "run_platform_backtest",
]
