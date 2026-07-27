# Funding 4h power study v1 — gate autopsy

**Date:** 2026-07-27  
**Reports:** `reports/hyp_f4h_*_v1_exploratory.json`  
**Parent daily autopsy:** `examples/batch/funding/GATE_AUTOPSY_V1.md`

## Headline

| | |
|--|--|
| Hyps | 6 / 6 |
| `passed_val` | **0** |
| Min val trades | **63** (all above `min_trades=30`) |
| Live registry | No |

## Per-hyp (val)

| Hyp | n_tr | Sharpe | CI lo | Main failures |
|-----|-----:|-------:|------:|---------------|
| `hyp_f4h_high_flat` | 101 | 0.59 | −0.77 | WF; bootstrap |
| `hyp_f4h_trend_and_not_high` | 101 | 0.59 | −0.77 | WF; bootstrap |
| `hyp_f4h_high_exit_only` | 285 | −0.01 | −1.32 | Sharpe; WF; bootstrap; skeptical; 2× cost |
| `hyp_f4h_pos_flat` | 63 | 0.16 | −1.43 | Sharpe; bootstrap; 2× cost |
| `hyp_f4h_chg_up_flat` | 290 | −0.88 | −2.15 | fee_fragile; Sharpe; maxDD; overfit gap; WF |
| `hyp_f4h_z_high_flat` | 332 | −0.40 | −1.73 | fee_fragile; Sharpe; maxDD; WF; bootstrap |

## Scientific conclusion

1. **Power was not the blocker** for daily near-misses (`high_flat` / `trend_and_not_high`): 4h delivers ample trades and still fails robustness gates.  
2. Funding **level / change / z** long-only filters on this true funding series do not survive frozen gates at **daily or 4h** under pre-registered budgets.  
3. Retire further **ad-hoc** funding long-only filter mining on these horizons. Optional future work only via **new** economic claims (e.g. different venue, short-side, interaction with OI) with fresh multiplicity.

## Process

Do **not** expand the 6-hyp lock or retune thresholds on the same 4h+funding data.
