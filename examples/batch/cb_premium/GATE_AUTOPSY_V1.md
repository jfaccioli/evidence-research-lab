# Gate autopsy — cb_premium

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_cbp_hi_ext_flat` | failed_val | 43 | 1.207 | -0.439 | -0.047 | bootstrap sharpe CI lo -0.047 < 0.0 |
| `hyp_cbp_lo_ext_long` | failed_val | 39 | 0.536 | -0.976 | -0.710 | bootstrap sharpe CI lo -0.710 < 0.0 |
| `hyp_cbp_neg_flat` | failed_val | 51 | 0.939 | -0.713 | -0.329 | bootstrap sharpe CI lo -0.329 < 0.0 |
| `hyp_cbp_pos_trend` | failed_val | 41 | 1.287 | -0.070 | -0.040 | bootstrap sharpe CI lo -0.040 < 0.0 |
| `hyp_cbp_z_high_flat` | failed_val | 22 | 1.639 | 0.048 | 0.518 | n_trades 22 < min_trades 30 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
