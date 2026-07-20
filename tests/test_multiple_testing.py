from crl.research.stats.multiple_testing import evaluate_multiple_testing


def test_more_trials_harder_bonferroni():
    a = evaluate_multiple_testing(sharpe_point=1.0, n_obs=500, n_family=1, n_global=1)
    b = evaluate_multiple_testing(sharpe_point=1.0, n_obs=500, n_family=100, n_global=100)
    assert b.bonferroni_alpha < a.bonferroni_alpha
    assert b.deflated_sharpe <= a.deflated_sharpe + 1e-9


def test_note_present():
    r = evaluate_multiple_testing(sharpe_point=0.5, n_obs=200, n_family=54, n_global=54)
    assert "n_family=54" in r.note
