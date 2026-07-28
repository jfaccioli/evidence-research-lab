# Gate autopsy — trend_quality

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_tq_mom_stack` | failed_val | 26 | 1.228 | -0.181 | -0.207 | n_trades 26 < min_trades 30; bootstrap sharpe CI lo -0.207 < 0.0 |
| `hyp_tq_stack_quiet` | failed_val | 7 | 0.939 | -0.456 | -0.311 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (7 |
| `hyp_tq_stack_volok` | failed_val | 57 | 0.393 | -0.992 | -0.919 | bootstrap sharpe CI lo -0.919 < 0.0 |
| `hyp_tq_trail_stack` | failed_val | 7 | 1.379 | 0.245 | 0.088 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (7 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
