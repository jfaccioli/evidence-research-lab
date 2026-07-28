# Gate autopsy — stablecoin_flow

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_sc_hi_ext_long` | failed_val | 72 | 0.438 | -1.015 | -1.072 | bootstrap sharpe CI lo -1.072 < 0.0; 2x cost stress sharpe -0.153 < 0 |
| `hyp_sc_lo_ext_flat` | failed_val | 53 | -1.000 | -1.421 | -2.302 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_sc_neg_flat` | failed_val | 124 | 0.430 | -0.965 | -0.804 | bootstrap sharpe CI lo -0.804 < 0.0; 2x cost stress sharpe -0.196 < 0 |
| `hyp_sc_pos_trend` | failed_val | 85 | 0.818 | -0.749 | -0.681 | bootstrap sharpe CI lo -0.681 < 0.0 |
| `hyp_sc_z_high_long` | failed_val | 34 | 0.573 | -1.009 | -0.728 | bootstrap sharpe CI lo -0.728 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
