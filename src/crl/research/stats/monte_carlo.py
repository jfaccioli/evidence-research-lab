"""Trade-sequence Monte Carlo for path / sequence risk."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MonteCarloResult:
    terminal_mean: float
    terminal_p5: float
    terminal_p50: float
    max_dd_mean: float
    max_dd_p95: float
    frac_dd_breach: float
    frac_underperform_bh: float


def _max_dd_from_returns(rets: np.ndarray) -> float:
    equity = np.cumprod(1.0 + rets)
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0
    return float(abs(dd.min())) if len(dd) else 0.0


def trade_sequence_mc(
    trade_returns: np.ndarray,
    *,
    n_sims: int = 500,
    seed: int = 42,
    dd_limit: float = 0.55,
    bh_terminal: float | None = None,
    block: int = 3,
) -> MonteCarloResult:
    """Resample trade returns in blocks; measure DD and terminal wealth."""
    x = np.asarray(trade_returns, dtype=float)
    n = len(x)
    if n == 0:
        return MonteCarloResult(1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0)

    rng = np.random.default_rng(seed)
    terminals = []
    dds = []
    block = max(1, min(block, n))

    for _ in range(n_sims):
        # stationary-ish block resample
        idx = []
        while len(idx) < n:
            s = int(rng.integers(0, n))
            for k in range(block):
                idx.append((s + k) % n)
                if len(idx) >= n:
                    break
        sample = x[np.array(idx[:n])]
        terminal = float(np.prod(1.0 + sample))
        terminals.append(terminal)
        dds.append(_max_dd_from_returns(sample))

    term = np.array(terminals)
    dda = np.array(dds)
    frac_breach = float((dda > dd_limit).mean())
    if bh_terminal is not None:
        frac_under = float((term < bh_terminal).mean())
    else:
        frac_under = float("nan")

    return MonteCarloResult(
        terminal_mean=float(term.mean()),
        terminal_p5=float(np.quantile(term, 0.05)),
        terminal_p50=float(np.quantile(term, 0.50)),
        max_dd_mean=float(dda.mean()),
        max_dd_p95=float(np.quantile(dda, 0.95)),
        frac_dd_breach=frac_breach,
        frac_underperform_bh=frac_under,
    )
