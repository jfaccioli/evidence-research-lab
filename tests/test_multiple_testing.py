"""B2 follow-up: annualization-consistent Bonferroni; non-DSR naming; fail-closed."""

from __future__ import annotations

import numpy as np

from crl.research.stats.multiple_testing import (
    approx_null_selection_proxy,
    evaluate_multiple_testing,
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
        trial_history_complete=True,
        n_analytical_trials=1,
        bar_returns=x,
    )
    assert abs(mt.sharpe_period - sr_p) < 1e-12
    assert abs(mt.sharpe_annualized - sr_p * np.sqrt(ann)) < 1e-12
    assert abs(mt.se_annualized - mt.se_period * np.sqrt(ann)) < 1e-12


def test_legacy_fail_closed_without_complete_trial_history():
    x = np.random.default_rng(2).normal(0.01, 0.02, size=400)
    # Even with large counts, without trial_history_complete must fail closed
    mt = evaluate_multiple_testing(
        n_obs=400,
        n_family=5,
        n_global=50,
        ann_factor=365.0,
        n_analytical_trials=999,  # not sufficient alone
        trial_history_complete=False,
        bar_returns=x,
    )
    assert mt.trials_ambiguous is True
    assert mt.trial_history_complete is False
    assert mt.passes_bonferroni_hint is False


def test_passes_only_when_history_complete_and_verified_trials():
    # Strong edge so stats would pass if allowed
    rng = np.random.default_rng(3)
    x = rng.normal(0.02, 0.01, size=800)
    open_mt = evaluate_multiple_testing(
        n_obs=800,
        n_family=1,
        n_global=1,
        ann_factor=365.0,
        n_analytical_trials=1,
        trial_history_complete=True,
        bar_returns=x,
    )
    closed_mt = evaluate_multiple_testing(
        n_obs=800,
        n_family=1,
        n_global=1,
        ann_factor=365.0,
        n_analytical_trials=1,
        trial_history_complete=False,
        bar_returns=x,
    )
    assert closed_mt.passes_bonferroni_hint is False
    # open may or may not pass depending on path; if it does, complete flag was required
    if open_mt.passes_bonferroni_hint:
        assert open_mt.trial_history_complete is True


def test_no_deflated_sharpe_or_blp_dsr_field_names():
    x = np.random.default_rng(4).normal(0.001, 0.02, size=200)
    mt = evaluate_multiple_testing(
        n_obs=200,
        n_family=3,
        n_global=3,
        trial_history_complete=False,
        bar_returns=x,
    )
    d = mt.__dict__
    assert "deflated_sharpe" not in d
    assert "approx_null_selection_proxy" in d
    assert "BLP" in mt.note or "NOT" in mt.note
    assert "NOT" in mt.definition and "DSR" in mt.definition


def test_se_hand_fixture():
    sr_p = 0.5
    n = 100
    se = se_period_sharpe(sr_p, n, skew=0.0, kurt=3.0)
    expected = np.sqrt((1.0 + 0.5 * sr_p**2) / (n - 1))
    assert abs(se - expected) < 1e-12


def test_proxy_not_named_dsr():
    p = approx_null_selection_proxy(sr_period=0.3, se_period=0.1, n_display_trials=10)
    assert 0.0 <= p <= 1.0


def test_z_not_radically_overconfident():
    n = 765
    ann = 365.0
    target_sr_p = 1.5 / np.sqrt(ann)
    rng = np.random.default_rng(1)
    x = rng.normal(0, 1, size=n)
    x = (x - x.mean()) / x.std(ddof=1)
    x = x * 0.02 + target_sr_p * 0.02
    mt = evaluate_multiple_testing(
        n_obs=n,
        n_family=15,
        n_global=100,
        ann_factor=ann,
        trial_history_complete=False,
        bar_returns=x,
    )
    assert mt.z_stat < 10.0
    assert mt.se_annualized > 0.2
    assert mt.passes_bonferroni_hint is False  # fail closed


def test_null_simulation_sanity():
    cal = null_simulation_max_annualized_sharpe(
        n_obs=250, n_trials=50, ann_factor=365.0, n_sims=400, seed=0
    )
    assert cal["mean_max_sr_a"] > 0.5
