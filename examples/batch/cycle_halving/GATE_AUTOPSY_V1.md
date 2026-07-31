# Gate autopsy — cycle_halving

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_cyc_post500_long` | failed_val | 2 | -0.589 | -1.507 | -1.775 | n_trades 2 < min_trades 30; primary sharpe_after_cost -0.589 < 0.2; bootstrap sh |
| `hyp_cyc_pre365_long` | failed_val | 1 | 1.444 | 0.307 | 0.274 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_cyc_pre500_long` | failed_val | 1 | 1.857 | 1.777 | 0.506 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_cyc_pre500_trend` | failed_val | 3 | 1.594 | 0.902 | 0.357 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (3 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
