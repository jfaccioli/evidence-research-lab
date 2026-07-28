# Gate autopsy — hold_4h

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_h4h_ema200` | failed_val | 62 | 1.041 | 0.340 | -0.373 | wf_positive_frac 0.50 < 0.6; bootstrap sharpe CI lo -0.373 < 0.0 |
| `hyp_h4h_sma200_quiet` | failed_val | 89 | 0.294 | -0.511 | -1.149 | wf_positive_frac 0.49 < 0.6; bootstrap sharpe CI lo -1.149 < 0.0; 2x cost stress |
| `hyp_h4h_sma200_quiet` | failed_val | 89 | 0.294 | -0.511 | -1.149 | wf_positive_frac 0.49 < 0.6; bootstrap sharpe CI lo -1.149 < 0.0; 2x cost stress |
| `hyp_h4h_sma50_200` | failed_val | 16 | 0.737 | -0.062 | -0.679 | n_trades 16 < min_trades 30; wf_positive_frac 0.51 < 0.6; bootstrap sharpe CI lo |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
