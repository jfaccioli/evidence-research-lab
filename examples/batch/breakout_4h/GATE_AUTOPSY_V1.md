# Gate autopsy — breakout_4h

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_b4h_donch20_mom` | failed_val | 73 | 0.686 | -0.182 | -0.775 | wf_positive_frac 0.48 < 0.6; bootstrap sharpe CI lo -0.775 < 0.0 |
| `hyp_b4h_donch20_quiet` | failed_val | 47 | 0.362 | -0.473 | -1.200 | overfit_gap 1.238 > 1.0; wf_positive_frac 0.58 < 0.6; bootstrap sharpe CI lo -1. |
| `hyp_b4h_donch20_vol` | failed_val | 106 | 1.021 | -0.062 | -0.457 | wf_positive_frac 0.55 < 0.6; bootstrap sharpe CI lo -0.457 < 0.0 |
| `hyp_b4h_donch55_trend` | failed_val | 20 | 1.021 | 0.176 | -0.333 | n_trades 20 < min_trades 30; wf_positive_frac 0.55 < 0.6; bootstrap sharpe CI lo |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
