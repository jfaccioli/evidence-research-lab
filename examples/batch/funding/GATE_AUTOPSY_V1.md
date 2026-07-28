# Gate autopsy — funding

**Mode:** exploratory  
**Reports found:** 10/10  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_funding_chg_up_flat` | failed_val | 82 | 1.180 | -0.181 | -0.084 | bootstrap sharpe CI lo -0.084 < 0.0 |
| `hyp_funding_high_exit_only` | failed_val | 43 | 1.163 | -0.049 | -0.109 | bootstrap sharpe CI lo -0.109 < 0.0 |
| `hyp_funding_high_flat` | failed_val | 19 | 1.481 | 0.324 | 0.231 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_funding_neg_long` | failed_val | 18 | 0.129 | -1.149 | -1.338 | n_trades 18 < min_trades 30; primary sharpe_after_cost 0.129 < 0.2; bootstrap sh |
| `hyp_funding_only_neg_mom` | failed_val | 24 | -0.354 | -1.220 | -1.841 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_funding_pos_flat` | failed_val | 18 | 0.898 | -0.949 | -0.808 | n_trades 18 < min_trades 30; bootstrap sharpe CI lo -0.808 < 0.0 |
| `hyp_funding_sum24_high_flat` | failed_val | 48 | 0.659 | -0.820 | -0.695 | bootstrap sharpe CI lo -0.695 < 0.0 |
| `hyp_funding_trend_and_not_high` | failed_val | 19 | 1.481 | 0.324 | 0.231 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (1 |
| `hyp_funding_z_high_flat` | failed_val | 66 | 0.500 | -0.904 | -0.736 | bootstrap sharpe CI lo -0.736 < 0.0 |
| `hyp_funding_z_low_long` | failed_val | 23 | -0.792 | -1.266 | -2.021 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
