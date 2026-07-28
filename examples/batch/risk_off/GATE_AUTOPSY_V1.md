# Gate autopsy — risk_off

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_ro_exit_volspike` | failed_val | 50 | 0.854 | -0.513 | -0.521 | bootstrap sharpe CI lo -0.521 < 0.0 |
| `hyp_ro_flat_highvol` | failed_val | 7 | 1.379 | 0.245 | 0.088 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (7 |
| `hyp_ro_mom_quiet` | failed_val | 45 | 0.931 | -0.444 | -0.300 | bootstrap sharpe CI lo -0.300 < 0.0 |
| `hyp_ro_trail_quiet` | failed_val | 15 | 1.050 | 0.017 | -0.350 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
