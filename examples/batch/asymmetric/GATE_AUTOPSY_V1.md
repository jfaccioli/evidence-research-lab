# Gate autopsy — asymmetric

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_asy_avoid_underwater_vol` | failed_val | 25 | 1.133 | -0.287 | -0.162 | n_trades 25 < min_trades 30; bootstrap sharpe CI lo -0.162 < 0.0 |
| `hyp_asy_donch_quiet` | failed_val | 4 | 1.156 | -0.288 | -0.154 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (4 |
| `hyp_asy_mom_flat_extension` | failed_val | 74 | 0.490 | -0.928 | -0.621 | bootstrap sharpe CI lo -0.621 < 0.0 |
| `hyp_asy_trail_in_trend` | failed_val | 3 | 1.536 | 0.822 | 0.337 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (3 |
| `hyp_asy_trend_cut_highvol` | failed_val | 7 | 1.379 | 0.245 | 0.088 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (7 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
