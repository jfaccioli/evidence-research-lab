"""B2: annualization-consistent DSR / Bonferroni reference tests."""

from __future__ import annotations

import numpy as np
import pytest

from crl.research.stats.multiple_testing import (
    deflated_sharpe_ratio,
    evaluate_multiple_testing,
    expected_max_null_period_sharpe,
    null_simulation_max_annualized_sharpe,
    period_sharpe_from_returns,
    se_period_sharpe,
)


def test_period_to_annualized_consistency():
    rng = np.random.default_rng(0)
    x = rng.normal(0.001, 0.02, size=500)
    sr_p, n = period_sharpe_from_returns(x)
    ann = 365.0
    mt = evaluate_multiple_testing(
        n_obs=n,
        n_family=1,
        n_global=1,
        ann_factor=ann,
        n_analytical_trials=1,
        bar_returns=x,
    )
    assert abs(mt.sharpe_period - sr_p) < 1e-12
    assert abs(mt.sharpe_annualized - sr_p * np.sqrt(ann)) < 1e-12
    assert abs(mt.se_annualized - mt.se_period * np.sqrt(ann)) < 1e-12
    # z identical either way
    assert abs(mt.z_stat - mt.sharpe_period / mt.se_period) < 1e-12


def test_mis_scaled_formula_rejected():
    """Old bug: se_a used se_p formula on annualized SR → huge z. New z must be moderate."""
    # Construct returns with annualized Sharpe roughly ~1.5
    n = 765
    ann = 365.0
    # target SR_p = 1.5/sqrt(365)
    target_sr_p = 1.5 / np.sqrt(ann)
    rng = np.random.default_rng(1)
    x = rng.normal(0, 1, size=n)
    x = (x - x.mean()) / x.std(ddof=1)
    x = x * 0.02 + target_sr_p * 0.02  # mean/std ≈ target_sr_p
    mt = evaluate_multiple_testing(
        n_obs=n,
        n_family=15,
        n_global=100,
        ann_factor=ann,
        n_analytical_trials=15,
        bar_returns=x,
    )
    # Old code gave z~28; correct z for SR~1.5 annual is order ~1-3 for n=765
    assert mt.z_stat < 10.0
    assert mt.se_annualized > 0.2  # not ~0.05


def test_fail_closed_without_analytical_trials():
    x = np.random.default_rng(2).normal(0.01, 0.02, size=400)
    mt = evaluate_multiple_testing(
        n_obs=400,
        n_family=5,
        n_global=50,
        ann_factor=365.0,
        n_analytical_trials=None,  # ambiguous
        bar_returns=x,
    )
    assert mt.trials_ambiguous is True
    assert mt.passes_bonferroni_hint is False


def test_bonferroni_tightens_with_more_trials():
    x = np.random.default_rng(3).normal(0.002, 0.02, size=800)
    a = evaluate_multiple_testing(
        n_obs=800,
        n_family=1,
        n_global=1,
        ann_factor=365.0,
        n_analytical_trials=1,
        bar_returns=x,
    )
    b = evaluate_multiple_testing(
        n_obs=800,
        n_family=1,
        n_global=1,
        ann_factor=365.0,
        n_analytical_trials=100,
        bar_returns=x,
    )
    assert b.bonferroni_alpha < a.bonferroni_alpha
    assert b.deflated_sharpe <= a.deflated_sharpe + 1e-9


def test_published_style_se_fixture():
    """Hand fixture: n=100, SR_p=0.5, skew=0, kurt=3 → se_p known."""
    sr_p = 0.5
    n = 100
    se = se_period_sharpe(sr_p, n, skew=0.0, kurt=3.0)
    expected = np.sqrt((1.0 + 0.5 * sr_p**2) / (n - 1))
    assert abs(se - expected) < 1e-12


def test_dsr_monotone_in_trials():
    se = 0.1
    sr = 0.3
    d1 = deflated_sharpe_ratio(sr_period=sr, se_period=se, n_trials=1)
    d50 = deflated_sharpe_ratio(sr_period=sr, se_period=se, n_trials=50)
    assert d50 < d1


def test_null_simulation_calibration_sanity():
    """Max SR among many null trials should exceed single-trial typical SR."""
    cal = null_simulation_max_annualized_sharpe(
        n_obs=250, n_trials=50, ann_factor=365.0, n_sims=500, seed=0
    )
    # Mean max annualized Sharpe under null should be clearly positive
    assert cal["mean_max_sr_a"] > 0.5
    # And DSR SR_0 scaling: se_p ~ 1/sqrt(n) for SR_p~0 → se_a ~ sqrt(ann/n)
    se_p = np.sqrt(1.0 / 249)
    sr0_a = expected_max_null_period_sharpe(50, se_p) * np.sqrt(365)
    # simulation mean max should be same order as analytic approx
    assert abs(cal["mean_max_sr_a"] - sr0_a) / sr0_a < 0.5


def test_definition_string_present():
    x = np.ones(50) * 0.001
    x = x + np.random.default_rng(0).normal(0, 0.01, 50)
    mt = evaluate_multiple_testing(
        n_obs=50,
        n_family=2,
        n_global=2,
        n_analytical_trials=2,
        bar_returns=x,
        ann_factor=365.0,
    )
    assert "SR_p" in mt.definition
    assert "fail_closed" in mt.definition
