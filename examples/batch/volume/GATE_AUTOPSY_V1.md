# Gate autopsy — volume

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_vol_dry_avoid` | failed_val | 83 | -0.097 | -1.318 | -1.446 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_vol_high_trend` | failed_val | 55 | 1.088 | -0.455 | -0.174 | bootstrap sharpe CI lo -0.174 < 0.0 |
| `hyp_vol_thrust_mom` | failed_val | 35 | 0.688 | -0.864 | -0.658 | wf_positive_frac 0.56 < 0.6; bootstrap sharpe CI lo -0.658 < 0.0 |
| `hyp_vol_z60_trend` | failed_val | 62 | 0.719 | -0.756 | -0.597 | bootstrap sharpe CI lo -0.597 < 0.0 |
| `hyp_vol_z_trend` | failed_val | 76 | 0.478 | -0.944 | -0.691 | bootstrap sharpe CI lo -0.691 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
