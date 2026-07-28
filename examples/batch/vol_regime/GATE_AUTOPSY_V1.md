# Gate autopsy — vol_regime

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 1

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_vr_calm_mom` | failed_val | 45 | 0.931 | -0.444 | -0.300 | bootstrap sharpe CI lo -0.300 < 0.0 |
| `hyp_vr_exit_volspike` | passed_val | 33 | 1.493 | 0.611 | 0.179 |  |
| `hyp_vr_highvol_mom_only` | failed_val | 15 | 0.136 | -1.144 | -1.251 | n_trades 15 < min_trades 30; primary sharpe_after_cost 0.136 < 0.2; wf_positive_ |
| `hyp_vr_only_lowvol` | failed_val | 7 | 1.379 | 0.245 | 0.088 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (7 |
| `hyp_vr_vol_chg_avoid` | failed_val | 34 | 0.593 | -0.825 | -0.604 | bootstrap sharpe CI lo -0.604 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
