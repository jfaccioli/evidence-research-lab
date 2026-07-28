# Gate autopsy — mr_trend

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_mr_avoid_ext_mom` | failed_val | 74 | 0.490 | -0.928 | -0.621 | bootstrap sharpe CI lo -0.621 < 0.0 |
| `hyp_mr_fade_z60` | failed_val | 0 | 0.000 | -1.163 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_mr_fade_z_trend` | failed_val | 13 | 0.898 | -0.787 | -0.324 | n_trades 13 < min_trades 30; wf_positive_frac 0.50 < 0.6; bootstrap sharpe CI lo |
| `hyp_mr_rejoin_sma20` | failed_val | 12 | 1.253 | -0.636 | -0.135 | n_trades 12 < min_trades 30; bootstrap sharpe CI lo -0.135 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
