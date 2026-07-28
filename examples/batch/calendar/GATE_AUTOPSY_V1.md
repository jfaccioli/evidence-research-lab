# Gate autopsy — calendar

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_cal_avoid_friday` | failed_val | 100 | 0.792 | -0.567 | -0.432 | bootstrap sharpe CI lo -0.432 < 0.0 |
| `hyp_cal_avoid_month_end` | failed_val | 17 | 1.465 | 0.578 | 0.188 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_cal_monday_mom` | failed_val | 61 | -1.345 | -1.539 | -2.347 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_cal_month_start` | failed_val | 16 | 0.169 | -1.135 | -1.235 | n_trades 16 < min_trades 30; primary sharpe_after_cost 0.169 < 0.2; wf_positive_ |
| `hyp_cal_weekday_only` | failed_val | 69 | 0.225 | -1.118 | -1.018 | bootstrap sharpe CI lo -1.018 < 0.0; 2x cost stress sharpe -0.108 < 0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
