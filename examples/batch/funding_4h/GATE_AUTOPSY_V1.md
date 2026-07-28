# Gate autopsy — funding_4h

**Mode:** exploratory  
**Reports found:** 6/6  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_f4h_chg_up_flat` | failed_val | 290 | -0.878 | -1.087 | -2.150 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_f4h_high_exit_only` | failed_val | 285 | -0.007 | -0.732 | -1.319 | primary sharpe_after_cost -0.007 < 0.2; wf_positive_frac 0.41 < 0.6; bootstrap s |
| `hyp_f4h_high_flat` | failed_val | 101 | 0.587 | -0.266 | -0.769 | wf_positive_frac 0.51 < 0.6; bootstrap sharpe CI lo -0.769 < 0.0 |
| `hyp_f4h_pos_flat` | failed_val | 63 | 0.162 | -0.589 | -1.431 | primary sharpe_after_cost 0.162 < 0.2; bootstrap sharpe CI lo -1.431 < 0.0; 2x c |
| `hyp_f4h_trend_and_not_high` | failed_val | 101 | 0.587 | -0.266 | -0.769 | wf_positive_frac 0.51 < 0.6; bootstrap sharpe CI lo -0.769 < 0.0 |
| `hyp_f4h_z_high_flat` | failed_val | 332 | -0.403 | -0.930 | -1.725 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
