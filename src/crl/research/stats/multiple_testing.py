"""Multiple-testing hygiene — annualization-consistent Bonferroni (P0).

================================================================================
DOCUMENTED DEFINITIONS
================================================================================

Period returns: r_t, t = 1..n (strategy bar net returns after costs)

  μ̂ = mean(r),  σ̂ = std(r, ddof=1)

**Per-period Sharpe** (rf = 0):
  SR_p = μ̂ / σ̂

**Annualized Sharpe** (A = periods/year, e.g. 365):
  SR_a = SR_p * sqrt(A)
  (matches metrics.compute_metrics)

**SE of per-period Sharpe** (Lo 2002 iid approximation, optional skew/kurt):
  se_p = sqrt( (1 + 0.5 SR_p² - γ3 SR_p + ((γ4-3)/4) SR_p²) / (n-1) )

**SE of annualized Sharpe** (consistent scaling):
  se_a = se_p * sqrt(A)

**One-sided z for H0: SR = 0**:
  z = SR_p / se_p = SR_a / se_a

**Bonferroni**:
  α' = α / N_trials
  p = 1 - Φ(z)

**N_trials / fail-closed policy (legacy programme)**:
  Historical analytical-trial completeness cannot be proven from registry
  counts alone (reruns, clones, abandoned peeks). Therefore:

  - Unless ``trial_history_complete=True`` is passed with an explicit
    ``n_analytical_trials``, ``trials_ambiguous=True`` and
    ``passes_bonferroni_hint=False`` (fail closed for promotion hygiene).
  - Registry-derived max(family, runs, global) must NOT be treated as a
    verified trial count that clears ambiguity.

**Approx null-selection proxy (NOT Bailey–López de Prado DSR)**:
  A descriptive hygiene number only:

    proxy = Φ( (SR_p - se_p * sqrt(2 log N_display)) / se_p )

  where N_display is a reporting placeholder (max of provided family/global
  counts). This is **not** the published BLP Deflated Sharpe Ratio: it does
  not use cross-trial Sharpe variance, the finite-N expected-maximum formula
  from the primary paper, or effective independent trials. Field name:
  ``approx_null_selection_proxy`` — never ``deflated_sharpe`` / "BLP DSR".
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
    n_trials_display: int
    n_obs: int
    ann_factor: float
    sharpe_period: float
    sharpe_annualized: float
    se_period: float
    se_annualized: float
    z_stat: float
    p_value_one_sided: float
    bonferroni_alpha: float
    # NOT BLP DSR — see module docstring
    approx_null_selection_proxy: float
    passes_bonferroni_hint: bool
    trials_ambiguous: bool
    trial_history_complete: bool
    definition: str
    note: str

    @property
    def sharpe_point(self) -> float:
        """Back-compat: annualized Sharpe point estimate."""
        return self.sharpe_annualized

    @property
    def n_trials(self) -> int:
        return self.n_trials_display


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
    if n < 3:
        return float("inf")
    var = (
        1.0
        + 0.5 * sr_p**2
        - skew * sr_p
        + ((kurt - 3.0) / 4.0) * sr_p**2
    ) / (n - 1)
    return sqrt(max(var, 1e-18))


def approx_null_selection_proxy(
    *,
    sr_period: float,
    se_period: float,
    n_display_trials: int,
) -> float:
    """Descriptive proxy only — NOT the published Bailey–López de Prado DSR."""
    if not np.isfinite(se_period) or se_period <= 0:
        return 0.0
    n = max(int(n_display_trials), 1)
    # Crude single-path adjustment; documented as non-DSR
    penalty = se_period * sqrt(2.0 * log(n)) if n > 1 else 0.0
    z = (sr_period - penalty) / se_period
    return float(_phi(z))


def evaluate_multiple_testing(
    *,
    sharpe_point: float | None = None,
    n_obs: int,
    n_family: int,
    n_global: int,
    ann_factor: float = 365.0,
    n_analytical_trials: int | None = None,
    trial_history_complete: bool = False,
    bar_returns: np.ndarray | None = None,
    skew: float | None = None,
    kurt: float | None = None,
    alpha: float = 0.05,
    min_proxy: float = 0.5,
) -> MultipleTestingResult:
    """Annualization-consistent Bonferroni + fail-closed legacy trial policy.

    ``passes_bonferroni_hint`` is True only if:
      - trial_history_complete is True, AND
      - n_analytical_trials is a positive verified count, AND
      - one-sided p < α/N and SR_a > 0 and approx proxy >= min_proxy.

    For the legacy daily price-only programme, callers must leave
    trial_history_complete=False so promotion hygiene fails closed.
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
                m = x.mean()
                s = x.std(ddof=1) + 1e-18
                zsc = (x - m) / s
                if skew is None:
                    skew = float(np.mean(zsc**3))
                if kurt is None:
                    kurt = float(np.mean(zsc**4))
    else:
        if sharpe_point is None:
            raise ValueError("Provide sharpe_point (annualized) or bar_returns")
        sr_p = float(sharpe_point) / sqrt(af)

    skew = 0.0 if skew is None else float(skew)
    kurt = 3.0 if kurt is None else float(kurt)

    se_p = se_period_sharpe(sr_p, n, skew=skew, kurt=kurt)
    se_a = se_p * sqrt(af)
    sr_a = sr_p * sqrt(af)
    z = sr_p / se_p if se_p > 0 and np.isfinite(se_p) else 0.0
    p_one = 1.0 - _phi(z)

    # Display N for reporting only — not a verified analytical trial census
    n_display = max(int(n_family), int(n_global), 1)
    if n_analytical_trials is not None and int(n_analytical_trials) >= 1:
        n_display = max(n_display, int(n_analytical_trials))

    # Fail closed unless completeness is explicitly proven
    complete = bool(trial_history_complete) and (
        n_analytical_trials is not None and int(n_analytical_trials) >= 1
    )
    trials_ambiguous = not complete
    n_for_bonf = (
        int(n_analytical_trials)
        if complete
        else n_display  # reporting only; cannot unlock pass
    )
    bonf = alpha / max(n_for_bonf, 1)

    proxy = approx_null_selection_proxy(
        sr_period=sr_p, se_period=se_p, n_display_trials=n_display
    )

    passes = (
        complete
        and (p_one < bonf)
        and (sr_a > 0)
        and (proxy >= min_proxy)
    )

    definition = (
        "SR_p=mean/std(ddof=1); SR_a=SR_p*sqrt(ann); "
        "se_p=sqrt((1+0.5 SR_p^2 - skew SR_p + ((kurt-3)/4) SR_p^2)/(n-1)); "
        "se_a=se_p*sqrt(ann); z=SR_p/se_p; Bonferroni α'=α/N; "
        "approx_null_selection_proxy=Φ((SR_p - se_p*sqrt(2 log N_display))/se_p) "
        "[NOT published BLP DSR]; "
        "passes_bonferroni_hint only if trial_history_complete and verified "
        "n_analytical_trials (else fail closed)."
    )
    note = (
        f"n_family={n_family}, n_global={n_global}, n_display={n_display}, "
        f"n_obs={n}, ann={af:g}, SR_p={sr_p:.4f}, SR_a={sr_a:.4f}, "
        f"se_p={se_p:.4g}, se_a={se_a:.4g}, z={z:.3f}, p={p_one:.4g}, "
        f"α'={bonf:.4g}, approx_null_selection_proxy={proxy:.3f}, "
        f"trials_ambiguous={trials_ambiguous}, "
        f"trial_history_complete={complete}. "
        "NOT BLP Deflated Sharpe. Hygiene only — fail closed without proven trial census."
    )

    return MultipleTestingResult(
        n_family=int(n_family),
        n_global=int(n_global),
        n_trials_display=n_display,
        n_obs=n,
        ann_factor=af,
        sharpe_period=float(sr_p),
        sharpe_annualized=float(sr_a),
        se_period=float(se_p),
        se_annualized=float(se_a),
        z_stat=float(z),
        p_value_one_sided=float(p_one),
        bonferroni_alpha=float(bonf),
        approx_null_selection_proxy=float(proxy),
        passes_bonferroni_hint=bool(passes),
        trials_ambiguous=bool(trials_ambiguous),
        trial_history_complete=bool(complete),
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
    """Monte Carlo calibration helper for Bonferroni z-scale (not BLP DSR)."""
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
