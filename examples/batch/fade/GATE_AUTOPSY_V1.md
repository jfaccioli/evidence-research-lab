# Gate autopsy — fade

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_fade_dist50_12pct` | failed_val | 2 | 1.263 | -0.927 | -0.222 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (2 |
| `hyp_fade_dist_sma20` | failed_val | 0 | 0.000 | -1.163 | 0.000 | n_trades 0 < min_trades 30; primary sharpe_after_cost 0.000 < 0.2; skeptical P(m |
| `hyp_fade_z20_exit_ext` | failed_val | 64 | 0.638 | -0.781 | -0.510 | bootstrap sharpe CI lo -0.510 < 0.0 |
| `hyp_fade_z20_exit_ext` | failed_val | 64 | 0.638 | -0.781 | -0.510 | bootstrap sharpe CI lo -0.510 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
