# Gate autopsy — polymarket

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_pm_hi_ext_flat` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_pm_high_flat` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_pm_low_long` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; wf_positive_f |
| `hyp_pm_pos_trend` | failed_val | 4 | -1.422 | 0.077 | -5.678 | n_trades 4 < min_trades 30; primary sharpe_after_cost -1.422 < 0.2; overfit_gap  |
| `hyp_pm_z_high_flat` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
