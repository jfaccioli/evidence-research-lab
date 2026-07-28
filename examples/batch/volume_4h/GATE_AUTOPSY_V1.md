# Gate autopsy — volume_4h

**Mode:** exploratory  
**Reports found:** 4/4  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_v4h_dry_avoid` | failed_val | 455 | -0.965 | -1.142 | -2.467 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_v4h_high_trend` | failed_val | 323 | -0.471 | -0.882 | -1.798 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_v4h_thrust_mom` | failed_val | 224 | -0.204 | -0.748 | -1.709 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_v4h_z_trend` | failed_val | 426 | -1.224 | -1.160 | -2.777 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
