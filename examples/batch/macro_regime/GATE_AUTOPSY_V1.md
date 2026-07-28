# Gate autopsy — macro_regime

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_mac_easy_long` | failed_val | 9 | 1.049 | -0.735 | -0.254 | n_trades 9 < min_trades 30; bootstrap sharpe CI lo -0.254 < 0.0 |
| `hyp_mac_easy_trend` | failed_val | 11 | 1.481 | -0.457 | -0.001 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_mac_stress_flat` | failed_val | 26 | 0.145 | -1.224 | -1.140 | n_trades 26 < min_trades 30; primary sharpe_after_cost 0.145 < 0.2; bootstrap sh |
| `hyp_mac_usd_high_flat` | failed_val | 1 | 0.925 | -0.086 | -0.359 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_mac_y2_up_flat` | failed_val | 85 | -0.489 | -1.623 | -1.767 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
