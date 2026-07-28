# Gate autopsy — herding

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_herd_ema_stack` | failed_val | 19 | 1.357 | 0.194 | 0.136 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_herd_mom_trend` | failed_val | 12 | 1.291 | 0.155 | 0.061 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_herd_sma200_volok` | failed_val | 59 | 0.648 | -0.760 | -0.654 | bootstrap sharpe CI lo -0.654 < 0.0 |
| `hyp_herd_stack` | failed_val | 11 | 1.090 | -0.306 | -0.106 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
