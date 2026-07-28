# Gate autopsy — participation

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_part_break_vol` | failed_val | 19 | 0.748 | -0.880 | -0.624 | n_trades 19 < min_trades 30; bootstrap sharpe CI lo -0.624 < 0.0 |
| `hyp_part_quiet_not` | failed_val | 55 | 0.103 | -1.179 | -1.260 | primary sharpe_after_cost 0.103 < 0.2; bootstrap sharpe CI lo -1.260 < 0.0; 2x c |
| `hyp_part_thrust_trend` | failed_val | 43 | 1.188 | -0.423 | -0.004 | bootstrap sharpe CI lo -0.004 < 0.0 |
| `hyp_part_vol_trend` | failed_val | 41 | 0.513 | -0.968 | -0.774 | bootstrap sharpe CI lo -0.774 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
