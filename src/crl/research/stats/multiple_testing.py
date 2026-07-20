"""Multiple-testing hygiene — annualization-consistent reference implementation.

================================================================================
MATHEMATICAL DEFINITIONS (P0 reference — do not "tune" ad hoc)
================================================================================

Period returns: r_t, t = 1..n  (strategy bar net returns after costs)

Sample mean and std (ddof=1):
  μ̂ = (1/n) Σ r_t
  σ̂ = sqrt( Σ (r_t - μ̂)² / (n - 1) )

**Per-period Sharpe** (risk-free = 0):
  SR_p = μ̂ / σ̂     (undefined / 0 if σ̂ = 0)

**Annualized Sharpe** (ann_factor = periods per year, e.g. 365 for daily crypto):
  SR_a = SR_p * sqrt(ann_factor)

This matches metrics.compute_metrics:
  sharpe_after_cost = (μ̂ * ann_factor) / (σ̂ * sqrt(ann_factor)) = SR_p * sqrt(ann_factor)

**Sampling SE of per-period Sharpe** (Lo 2002 / Bailey–López de Prado style,
iid returns; optional skew/kurt corrections):

  se(SR_p) = sqrt(
      (1 + 0.5 SR_p² - γ̂_3 SR_p + ((γ̂_4 - 3)/4) SR_p²) / (n - 1)
  )
  with γ̂_3 = skew, γ̂_4 = kurtosis (Pearson). Defaults γ̂_3=0, γ̂_4=3 recover
  se(SR_p) = sqrt( (1 + 0.5 SR_p²) / (n - 1) ).

**SE of annualized Sharpe** (consistent scaling):
  se(SR_a) = se(SR_p) * sqrt(ann_factor)

**z-test of H0: SR_a = 0** (equivalently SR_p = 0):
  z = SR_a / se(SR_a) = SR_p / se(SR_p)

**Bonferroni**:
  α' = α / N_trials
  reject H0 (one-sided SR>0) if p = 1 - Φ(z) < α' and SR_a > 0

**Deflated Sharpe (simplified BLP)**:
  E[max SR_p under N null trials] ≈ sqrt(2 log N) * se(SR_p)   (N>1), else 0
  More precisely we use expected max of N standard normals times se:
  SR_0 = se(SR_p) * sqrt(2 log N)   for N>1
  DSR = Φ( (SR_p - SR_0) / se(SR_p) )

  DSR is a *hygiene* score in [0,1], not a proof of edge.

**N_trials (fail-closed)**:
  N_trials = n_analytical_trials if provided and >= 1
  else N_trials = max(n_family, n_global, 1) AND pass_hint is forced False
  (ambiguous trial history must not pass multiple-testing hygiene).

Reruns and parameter variants that participated in selection should be counted
in n_analytical_trials by the caller (e.g. max(family hyps, family runs, global)).
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, log, sqrt
from typing import Any

import numpy as np


@dataclass
class MultipleTestingResult:
    n_family: int
    n_global: int
    n_trials: int
    n_obs: int
    ann_factor: float
    sharpe_period: float
    sharpe_annualized: float
    se_period: float
    se_annualized: float
    z_stat: float
    p_value_one_sided: float
    bonferroni_alpha: float
    deflated_sharpe: float
    passes_bonferroni_hint: bool
    trials_ambiguous: bool
    definition: str
    note: str

    # back-compat aliases used by reports
    @property
    def sharpe_point(self) -> float:
        return self.sharpe_annualized


def _phi(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def period_sharpe_from_returns(returns: np.ndarray) -> tuple[float, int]:
    x = np.asarray(returns, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return 0.0, n
    mu = float(x.mean())
    sig = float(x.std(ddof=1))
    if sig < 1e-18:
        return 0.0, n
    return mu / sig, n


def se_period_sharpe(
    sr_p: float,
    n: int,
    *,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> float:
    """Lo / BLP SE for the **per-period** Sharpe ratio."""
    if n < 3:
        return float("inf")
    # Non-normal correction terms (BLP eq. style)
    var = (
        1.0
        + 0.5 * sr_p**2
        - skew * sr_p
        + ((kurt - 3.0) / 4.0) * sr_p**2
    ) / (n - 1)
    return sqrt(max(var, 1e-18))


def expected_max_null_period_sharpe(n_trials: int, se_p: float) -> float:
    """E[max SR_p] under N iid nulls ≈ se_p * sqrt(2 log N)."""
    if n_trials <= 1 or not np.isfinite(se_p):
        return 0.0
    return float(se_p * sqrt(2.0 * log(n_trials)))


def deflated_sharpe_ratio(
    *,
    sr_period: float,
    se_period: float,
    n_trials: int,
) -> float:
    """DSR = Φ( (SR_p - SR_0) / se(SR_p) ) with SR_0 = E[max null SR_p]."""
    if not np.isfinite(se_period) or se_period <= 0:
        return 0.0
    sr0 = expected_max_null_period_sharpe(n_trials, se_period)
    z = (sr_period - sr0) / se_period
    return float(_phi(z))


def evaluate_multiple_testing(
    *,
    sharpe_point: float | None = None,
    n_obs: int,
    n_family: int,
    n_global: int,
    ann_factor: float = 365.0,
    n_analytical_trials: int | None = None,
    bar_returns: np.ndarray | None = None,
    skew: float | None = None,
    kurt: float | None = None,
    alpha: float = 0.05,
    min_dsr: float = 0.5,
) -> MultipleTestingResult:
    """Annualization-consistent multiple-testing hygiene.

    Prefer passing ``bar_returns`` so SR_p is computed from data. If only
    ``sharpe_point`` (annualized) is given, convert via SR_p = SR_a / sqrt(ann).
    """
    af = float(ann_factor) if ann_factor and ann_factor > 0 else 365.0
    n = int(n_obs)

    if bar_returns is not None:
        sr_p, n_from = period_sharpe_from_returns(np.asarray(bar_returns, dtype=float))
        n = n_from if n_from >= 3 else n
        if skew is None or kurt is None:
            x = np.asarray(bar_returns, dtype=float)
            x = x[np.isfinite(x)]
            if len(x) >= 4:
                # simple moment estimates
                m = x.mean()
                s = x.std(ddof=1) + 1e-18
                z = (x - m) / s
                skew = float(np.mean(z**3)) if skew is None else skew
                kurt = float(np.mean(z**4)) if kurt is None else kurt
    else:
        if sharpe_point is None:
            raise ValueError("Provide sharpe_point (annualized) or bar_returns")
        # Convert annualized point estimate to period Sharpe
        sr_p = float(sharpe_point) / sqrt(af)

    skew = 0.0 if skew is None else float(skew)
    kurt = 3.0 if kurt is None else float(kurt)

    se_p = se_period_sharpe(sr_p, n, skew=skew, kurt=kurt)
    se_a = se_p * sqrt(af)
    sr_a = sr_p * sqrt(af)
    z = sr_p / se_p if se_p > 0 and np.isfinite(se_p) else 0.0
    p_one = 1.0 - _phi(z)

    trials_ambiguous = False
    if n_analytical_trials is not None and int(n_analytical_trials) >= 1:
        n_trials = int(n_analytical_trials)
    else:
        # Fail closed: without an explicit analytical trial count, do not pass hygiene
        n_trials = max(int(n_family), int(n_global), 1)
        trials_ambiguous = True

    bonf = alpha / n_trials
    dsr = deflated_sharpe_ratio(sr_period=sr_p, se_period=se_p, n_trials=n_trials)

    passes = (
        (not trials_ambiguous)
        and (p_one < bonf)
        and (sr_a > 0)
        and (dsr >= min_dsr)
    )

    definition = (
        "SR_p=mean/std(ddof=1); SR_a=SR_p*sqrt(ann); "
        "se_p=sqrt((1+0.5 SR_p^2 - skew SR_p + ((kurt-3)/4) SR_p^2)/(n-1)); "
        "se_a=se_p*sqrt(ann); z=SR_p/se_p; "
        "Bonferroni α'=α/N_trials; DSR=Φ((SR_p - se_p*sqrt(2 log N))/se_p); "
        "fail_closed if n_analytical_trials omitted."
    )
    note = (
        f"n_family={n_family}, n_global={n_global}, n_trials={n_trials}, "
        f"n_obs={n}, ann={af:g}, SR_p={sr_p:.4f}, SR_a={sr_a:.4f}, "
        f"se_p={se_p:.4g}, se_a={se_a:.4g}, z={z:.3f}, p={p_one:.4g}, "
        f"α'={bonf:.4g}, DSR={dsr:.3f}, trials_ambiguous={trials_ambiguous}. "
        "Hygiene only — not proof of edge."
    )

    return MultipleTestingResult(
        n_family=int(n_family),
        n_global=int(n_global),
        n_trials=n_trials,
        n_obs=n,
        ann_factor=af,
        sharpe_period=float(sr_p),
        sharpe_annualized=float(sr_a),
        se_period=float(se_p),
        se_annualized=float(se_a),
        z_stat=float(z),
        p_value_one_sided=float(p_one),
        bonferroni_alpha=float(bonf),
        deflated_sharpe=float(dsr),
        passes_bonferroni_hint=bool(passes),
        trials_ambiguous=trials_ambiguous,
        definition=definition,
        note=note,
    )


def null_simulation_max_annualized_sharpe(
    *,
    n_obs: int,
    n_trials: int,
    ann_factor: float = 365.0,
    n_sims: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    """Monte Carlo: max annualized Sharpe among N_trials null paths (iid N(0,1) returns).

    Used for calibration tests only.
    """
    rng = np.random.default_rng(seed)
    maxima = []
    for _ in range(n_sims):
        best = -1e9
        for _k in range(n_trials):
            x = rng.normal(0.0, 1.0, size=n_obs)
            sr_p, _ = period_sharpe_from_returns(x)
            best = max(best, sr_p * sqrt(ann_factor))
        maxima.append(best)
    arr = np.asarray(maxima, dtype=float)
    return {
        "mean_max_sr_a": float(arr.mean()),
        "p95_max_sr_a": float(np.quantile(arr, 0.95)),
        "n_sims": n_sims,
        "n_trials": n_trials,
        "n_obs": n_obs,
    }
