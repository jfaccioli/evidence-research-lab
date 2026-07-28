# Gate autopsy — liquidations

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 1

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_liq_after_ext_long` | failed_val | 57 | 0.749 | -0.871 | -0.644 | bootstrap sharpe CI lo -0.644 < 0.0 |
| `hyp_liq_ext_flat` | failed_val | 57 | 0.167 | -1.133 | -1.327 | primary sharpe_after_cost 0.167 < 0.2; bootstrap sharpe CI lo -1.327 < 0.0; 2x c |
| `hyp_liq_hi_flat` | failed_val | 112 | 0.145 | -1.157 | -1.097 | primary sharpe_after_cost 0.145 < 0.2; bootstrap sharpe CI lo -1.097 < 0.0; 2x c |
| `hyp_liq_low_long` | passed_val | 79 | 1.448 | -0.162 | 0.129 |  |
| `hyp_liq_z_high_flat` | failed_val | 40 | 0.264 | -1.094 | -0.915 | bootstrap sharpe CI lo -0.915 < 0.0; 2x cost stress sharpe -0.084 < 0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
