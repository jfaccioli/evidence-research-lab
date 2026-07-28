# Gate autopsy — pm_panel

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_pmp_bull_trend` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_pmp_disp_flat` | failed_val | 1 | -0.835 | -0.020 | -3.786 | n_trades 1 < min_trades 30; primary sharpe_after_cost -0.835 < 0.2; overfit_gap  |
| `hyp_pmp_high_flat` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_pmp_low_long` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; wf_positive_f |
| `hyp_pmp_z_hi_flat` | failed_val | 0 | 0.000 | 0.160 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
