# Gate autopsy — atr_trail

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_atr_trail_mom20` | failed_val | 45 | 0.966 | -0.322 | -0.365 | bootstrap sharpe CI lo -0.365 < 0.0 |
| `hyp_atr_trail_only` | failed_val | 6 | 0.987 | 0.033 | -0.335 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (6 |
| `hyp_atr_trail_quiet` | failed_val | 15 | 1.050 | 0.017 | -0.350 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_atr_trail_sma100` | failed_val | 12 | 1.068 | -0.131 | -0.329 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_atr_trail_sma200` | failed_val | 3 | 1.536 | 0.822 | 0.337 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (3 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
