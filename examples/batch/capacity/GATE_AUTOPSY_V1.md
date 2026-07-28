# Gate autopsy — capacity

**Mode:** exploratory  
**Reports found:** 5/5  
**passed_val:** 0

| hypothesis | status | n_tr | sharpe | excess_bh | ci_lo | reasons |
|------------|--------|-----:|-------:|----------:|------:|---------|
| `hyp_cap_ema200_hold` | failed_val | 9 | 1.286 | 0.262 | 0.072 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (9 |
| `hyp_cap_lowvol_sma50` | failed_val | 21 | 0.786 | -0.615 | -0.591 | n_trades 21 < min_trades 30; bootstrap sharpe CI lo -0.591 < 0.0 |
| `hyp_cap_mom20_trend` | failed_val | 25 | 1.072 | -0.338 | -0.313 | n_trades 25 < min_trades 30; bootstrap sharpe CI lo -0.313 < 0.0 |
| `hyp_cap_sma200_hold` | failed_val | 3 | 1.519 | 0.788 | 0.313 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (3 |
| `hyp_cap_sma50_200_cross` | failed_val | 2 | 1.109 | -0.083 | -0.087 | reality: [economic_plausibility] Weak economic story / noise risk: few trades (2 |

## Process

- Frozen gates; no threshold mining on this lock.
- Autopsy is observational — not a promotion decision.
