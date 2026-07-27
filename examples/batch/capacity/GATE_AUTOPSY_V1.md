# Capacity tiny-friction v1 — gate autopsy

## Per-hyp (val, elevated costs)

| Hyp | n_tr | Sharpe | Main failures |
|-----|-----:|-------:|---------------|
| `hyp_cap_sma200_hold` | 3 | 1.52 | min_trades; reality few-trades |
| `hyp_cap_ema200_hold` | 9 | 1.29 | min_trades; reality few-trades |
| `hyp_cap_sma50_200_cross` | 2 | 1.11 | min_trades; reality; bootstrap |
| `hyp_cap_lowvol_sma50` | 21 | 0.79 | min_trades; bootstrap |
| `hyp_cap_mom20_trend` | 25 | 1.07 | min_trades; bootstrap |

## Side discovery (pipeline)

Sensitivity neighborhood rewrote `sma_50_above_200` → `sma_10_above_200` (compound name bug). **Fixed** in `sensitivity.py` (bare `sma_N` tokens only). Regression covered in tests.

## Conclusion

Programme-level null for this 5-hyp lock under elevated costs. Do not mine more SMA windows. Mechanism `capacity_tiny_friction` stance: **active / pivot** — evidence that sparse “pretty Sharpe” rules fail honest trade-count + friction gates for tiny capital.
