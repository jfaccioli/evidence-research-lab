# Gate autopsy — liquidity

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_liq_dip3_rebound` | failed_val | 15 | 0.993 | -0.830 | 0.021 | n_trades 15 < min_trades 30 |
| `hyp_liq_dip5_rebound` | failed_val | 8 | 0.678 | -0.948 | -0.395 | n_trades 8 < min_trades 30; bootstrap sharpe CI lo -0.395 < 0.0 |
| `hyp_liq_donch_panic_recover` | failed_val | 7 | 1.311 | -0.586 | -0.046 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (7 |
| `hyp_liq_highvol_fade` | failed_val | 11 | 0.008 | -1.201 | -0.874 | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction o |
| `hyp_liq_volume_dry_up` | failed_val | 45 | 0.810 | -0.821 | -0.416 | wf_positive_frac 0.44 < 0.6; bootstrap sharpe CI lo -0.416 < 0.0 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
