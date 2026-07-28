# Gate autopsy — mvrv

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_mvrv_high_flat` | failed_val | 8 | 1.475 | 0.659 | 0.224 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (8 |
| `hyp_mvrv_low_long` | failed_val | 3 | 0.920 | -0.991 | -1.473 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (3 |
| `hyp_mvrv_mid_trend` | failed_val | 12 | 1.803 | 1.083 | 0.614 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_mvrv_z_high_flat` | failed_val | 6 | 1.533 | 0.383 | 0.284 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (6 |
| `hyp_mvrv_z_low_long` | failed_val | 3 | 0.274 | -1.130 | -1.125 | n_trades 3 < min_trades 30; bootstrap sharpe CI lo -1.125 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
