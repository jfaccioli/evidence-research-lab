# Gate autopsy — breakout

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_bo_donch100` | failed_val | 1 | 1.475 | 0.708 | 0.321 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_bo_donch20_mom` | failed_val | 14 | 1.143 | -0.207 | -0.233 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_bo_donch20_quiet` | failed_val | 10 | 0.883 | -0.538 | -0.363 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_bo_donch20_vol` | failed_val | 24 | 0.526 | -0.943 | -0.837 | n_trades 24 < min_trades 30; bootstrap sharpe CI lo -0.837 < 0.0 |
| `hyp_bo_donch55_trend` | failed_val | 3 | 1.110 | -0.160 | -0.068 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (3 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
