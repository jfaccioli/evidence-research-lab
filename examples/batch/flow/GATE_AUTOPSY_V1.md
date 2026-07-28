# Gate autopsy — flow

**Mode:** exploratory  
**Reports found:** 8/8  
**passed_val:** 6

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_flow_exit_inflow` | passed_val | 76 | 1.447 | 0.444 | 0.168 |  |
| `hyp_flow_high_flat` | failed_val | 112 | 0.771 | -0.738 | -0.549 | bootstrap sharpe CI lo -0.549 < 0.0 |
| `hyp_flow_inflow_flat` | passed_val | 69 | 1.486 | 0.436 | 0.158 |  |
| `hyp_flow_into_flat` | failed_val | 114 | 0.877 | -0.656 | -0.436 | bootstrap sharpe CI lo -0.436 < 0.0 |
| `hyp_flow_outflow_long` | passed_val | 50 | 1.248 | -0.769 | 0.147 |  |
| `hyp_flow_trend_not_inflow` | passed_val | 69 | 1.486 | 0.436 | 0.158 |  |
| `hyp_flow_z_high_flat` | passed_val | 60 | 1.538 | 0.282 | 0.231 |  |
| `hyp_flow_z_low_long` | passed_val | 33 | 1.498 | -0.741 | 0.515 |  |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.


## Confirmatory (2026-07-28, CMD netflow)

All 6 exploratory `passed_val` hyps re-run in confirmatory mode with same series + frozen gates.

| id | status | test_sharpe (approx) |
|----|--------|----------------------|
| hyp_flow_exit_inflow | failed_test | ~-0.09 |
| hyp_flow_inflow_flat | failed_test | ~-0.33 |
| hyp_flow_outflow_long | failed_test | ~-0.09 |
| hyp_flow_trend_not_inflow | failed_test | ~-0.33 |
| hyp_flow_z_high_flat | failed_test | ~-0.08 |
| hyp_flow_z_low_long | failed_test | ~-0.68 |

**Candidates: 0.** Pattern matches prior programmes: val teases die on test + costs.
