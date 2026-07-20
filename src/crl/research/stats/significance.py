"""Block bootstrap of the *primary* metric (bar after-cost Sharpe).

Inference must target the same statistic used in gates — not a parallel
trade-Sharpe with a magic ann_trades_per_year.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from math import erf, sqrt


@dataclass
class BootstrapResult:
    sharpe_point: float
    sharpe_ci: tuple[float, float]
    mean_bar_ci: tuple[float, float]
    p_mean_gt_0_skeptical: float
    n_bars: int
    n_effective_hint: float
    ann_factor: float


def block_bootstrap_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    if n == 0:
        return np.array([], dtype=int)
    block = max(1, min(block, n))
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block + 1, 1), size=n_blocks)
    idx: list[int] = []
    for s in starts:
        for k in range(block):
            j = s + k
            if j >= n:
                break
            idx.append(j)
            if len(idx) >= n:
                return np.array(idx[:n], dtype=int)
    # pad if short
    while len(idx) < n:
        idx.append(int(rng.integers(0, n)))
    return np.array(idx[:n], dtype=int)


def _sharpe(rets: np.ndarray, ann_factor: float) -> float:
    if len(rets) < 3:
        return 0.0
    s = float(rets.std(ddof=1))
    if s < 1e-12:
        return 0.0
    return float(rets.mean() / s * np.sqrt(ann_factor))


def bootstrap_bar_sharpe(
    bar_returns: np.ndarray,
    *,
    ann_factor: float = 365.0,
    n_boot: int = 500,
    block: int | None = None,
    seed: int = 42,
) -> BootstrapResult:
    """Block-bootstrap the annualized Sharpe of the bar return series."""
    x = np.asarray(bar_returns, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    point = _sharpe(x, ann_factor)
    if n < 10:
        return BootstrapResult(
            sharpe_point=point,
            sharpe_ci=(point, point),
            mean_bar_ci=(0.0, 0.0),
            p_mean_gt_0_skeptical=0.5,
            n_bars=n,
            n_effective_hint=float(n),
            ann_factor=ann_factor,
        )

    # Default block ~5 trading days of dependence for daily; scale with n
    if block is None:
        block = max(5, min(20, n // 20))

    rng = np.random.default_rng(seed)
    sharpes = []
    means = []
    for _ in range(n_boot):
        idx = block_bootstrap_indices(n, block, rng)
        sample = x[idx]
        means.append(float(sample.mean()))
        sharpes.append(_sharpe(sample, ann_factor))

    means_a = np.array(means)
    sharpes_a = np.array(sharpes)
    mean_ci = (float(np.quantile(means_a, 0.025)), float(np.quantile(means_a, 0.975)))
    sharpe_ci = (float(np.quantile(sharpes_a, 0.025)), float(np.quantile(sharpes_a, 0.975)))

    sample_mean = float(x.mean())
    sample_var = float(x.var(ddof=1)) if n > 1 else 1.0
    prior_var = (2.0 * (np.sqrt(sample_var) + 1e-8)) ** 2
    post_var = 1.0 / (1.0 / prior_var + n / (sample_var + 1e-12))
    post_mean = post_var * (n * sample_mean / (sample_var + 1e-12))
    z = post_mean / sqrt(post_var + 1e-18)
    p_gt0 = 0.5 * (1.0 + erf(z / sqrt(2.0)))

    if n > 3:
        x0 = x - x.mean()
        ac1 = float(np.corrcoef(x0[:-1], x0[1:])[0, 1]) if np.std(x0[:-1]) > 0 else 0.0
        ac1 = max(-0.99, min(0.99, ac1))
        neff = n / (1.0 + 2.0 * max(0.0, ac1))
    else:
        neff = float(n)

    return BootstrapResult(
        sharpe_point=point,
        sharpe_ci=sharpe_ci,
        mean_bar_ci=mean_ci,
        p_mean_gt_0_skeptical=float(p_gt0),
        n_bars=n,
        n_effective_hint=float(neff),
        ann_factor=ann_factor,
    )


# Back-compat alias used by older tests / call sites
def bootstrap_trade_stats(
    trade_returns: np.ndarray,
    *,
    n_boot: int = 500,
    block: int = 5,
    seed: int = 42,
    ann_trades_per_year: float = 10.0,
) -> BootstrapResult:
    """Deprecated path: prefer bootstrap_bar_sharpe on bar returns.

    Still block-bootstraps the provided series as if they were bar returns
    with ann_factor=ann_trades_per_year (legacy).
    """
    return bootstrap_bar_sharpe(
        trade_returns,
        ann_factor=ann_trades_per_year,
        n_boot=n_boot,
        block=block,
        seed=seed,
    )
