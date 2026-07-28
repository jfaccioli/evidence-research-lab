# Gate autopsy — slow_fast

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_sf_accel10_30` | failed_val | 29 | 0.158 | -1.137 | -1.383 | n_trades 29 < min_trades 30; primary sharpe_after_cost 0.158 < 0.2; bootstrap sh |
| `hyp_sf_accel_neg_flat` | failed_val | 14 | 1.043 | -0.773 | -0.233 | n_trades 14 < min_trades 30; bootstrap sharpe CI lo -0.233 < 0.0 |
| `hyp_sf_accel_pos_trend` | failed_val | 14 | 1.043 | -0.773 | -0.233 | n_trades 14 < min_trades 30; bootstrap sharpe CI lo -0.233 < 0.0 |
| `hyp_sf_both_mom` | failed_val | 30 | 1.027 | -0.355 | -0.254 | bootstrap sharpe CI lo -0.254 < 0.0 |
| `hyp_sf_fast_above_slow` | failed_val | 6 | 1.002 | -0.764 | -0.418 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (6 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
