# Gate autopsy — oi

**Mode:** exploratory  
**Reports found:** 10/10  
**passed_val:** 1

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_oi_chg_pct_high_flat` | passed_val | 30 | 1.377 | 0.412 | 0.075 |  |
| `hyp_oi_falling_long` | failed_val | 123 | 0.271 | -1.083 | -1.128 | wf_positive_frac 0.56 < 0.6; bootstrap sharpe CI lo -1.128 < 0.0; 2x cost stress |
| `hyp_oi_high_exit_only` | failed_val | 232 | 0.474 | -0.941 | -0.894 | bootstrap sharpe CI lo -0.894 < 0.0; 2x cost stress sharpe -0.794 < 0 |
| `hyp_oi_high_flat` | failed_val | 0 | 0.000 | -1.163 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_oi_only_not_high_mom` | failed_val | 0 | 0.000 | -1.163 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_oi_rising_flat` | failed_val | 133 | 0.167 | -1.142 | -1.314 | primary sharpe_after_cost 0.167 < 0.2; bootstrap sharpe CI lo -1.314 < 0.0; 2x c |
| `hyp_oi_sum5_high_flat` | failed_val | 72 | 0.507 | -0.919 | -0.551 | bootstrap sharpe CI lo -0.551 < 0.0 |
| `hyp_oi_trend_and_not_high` | failed_val | 0 | 0.000 | -1.163 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_oi_z_high_flat` | failed_val | 54 | 0.856 | -0.590 | -0.482 | bootstrap sharpe CI lo -0.482 < 0.0 |
| `hyp_oi_z_low_long` | failed_val | 20 | 0.075 | -1.165 | -0.966 | n_trades 20 < min_trades 30; primary sharpe_after_cost 0.075 < 0.2; wf_positive_ |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
