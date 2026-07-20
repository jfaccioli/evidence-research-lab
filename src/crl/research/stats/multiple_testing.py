"""Multiple-testing controls for the research lab.

At scale, uncorrected discovery is the primary scientific failure mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, sqrt


@dataclass
class MultipleTestingResult:
    n_family: int
    n_global: int
    bonferroni_alpha: float
    deflated_sharpe: float
    sharpe_point: float
    passes_bonferroni_hint: bool
    note: str


def _phi(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def deflated_sharpe_ratio(
    sharpe: float,
    *,
    n_obs: int,
    n_trials: int,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> float:
    """Bailey & López de Prado style Deflated Sharpe Ratio (simplified).

    Returns estimated Prob(observed SR is true given n_trials selection).
    Implementation follows the common practical form; not a full paper replica
    but directionally correct for research hygiene.
    """
    if n_obs < 3 or n_trials < 1:
        return 0.0
    # Expected max SR under null ≈ (1-γ)Φ^{-1}(1-1/N) + γΦ^{-1}(1-1/(N e))
    # Use approximation E[max Z] ~ sqrt(2 log N)
    if n_trials == 1:
        e_max = 0.0
    else:
        e_max = sqrt(2.0 * log(n_trials))
    # Variance of SR estimator (Lo 2002 style rough)
    sr_var = (1.0 + 0.5 * sharpe**2 - skew * sharpe + ((kurt - 3) / 4.0) * sharpe**2) / max(
        n_obs, 1
    )
    sr_var = max(sr_var, 1e-12)
    # DSR ≈ Φ( (SR - E[max SR_null]) / se )
    z = (sharpe - e_max * sr_var**0.5 * 0.0 - e_max * 0.25) / sqrt(sr_var)
    # Soften: compare SR to expected max under N(0, se)
    se = sqrt(sr_var)
    z = (sharpe - e_max * se) / se if se > 0 else 0.0
    return float(_phi(z))


def evaluate_multiple_testing(
    *,
    sharpe_point: float,
    n_obs: int,
    n_family: int,
    n_global: int,
    alpha: float = 0.05,
    min_dsr: float = 0.5,
) -> MultipleTestingResult:
    n_trials = max(n_family, 1)
    bonf = alpha / n_trials
    # One-sided: treat SR/se as z; rough se for annualized SR on daily
    se = 1.0 / sqrt(max(n_obs, 1)) * 1.0  # very rough under unit vol
    # Better: se of Sharpe ≈ sqrt((1+0.5 SR^2)/n)
    se = sqrt((1.0 + 0.5 * sharpe_point**2) / max(n_obs, 1))
    # p-value under null SR=0
    z = sharpe_point / se if se > 0 else 0.0
    p = 1.0 - _phi(z)
    passes_bonf = p < bonf and sharpe_point > 0

    dsr = deflated_sharpe_ratio(sharpe_point, n_obs=n_obs, n_trials=n_trials)
    note = (
        f"n_family={n_family}, n_global={n_global}, Bonferroni α'={bonf:.4g}, "
        f"approx p(SR>0)={p:.4g}, DSR={dsr:.3f}. "
        "DSR/Bonferroni are hygiene, not proof of edge."
    )
    return MultipleTestingResult(
        n_family=n_family,
        n_global=n_global,
        bonferroni_alpha=bonf,
        deflated_sharpe=dsr,
        sharpe_point=sharpe_point,
        passes_bonferroni_hint=passes_bonf and dsr >= min_dsr,
        note=note,
    )
