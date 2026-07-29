# LEDA results log (scientific, not marketing)

**Updated:** 2026-07-29  
**Rule:** skill and exploratory economics only; **0 APPROVED**; **shadow not justified**.

## LEDA-1 `leda1_vol_risk` (Risk)

| Metric | BTC 1d pinned |
|--------|----------------|
| n | ~3206 |
| pearson rv_lag vs rv_next | **~0.96** |
| Interpretation | Strong **vol persistence** skill for risk layer |

Risk evidence channel is scientifically useful as a **veto input**, not directional alpha.

## LEDA-2 `leda2_trend` (Forecast)

| Metric | BTC 1d pinned |
|--------|----------------|
| pearson score vs fwd_ret | ~0.03 |
| mean fwd when score≥0.5 vs <0.5 | slightly positive but tiny |

Weak IC only — consistent with prior TSMOM nulls under costs.

## LEDA-4 thin stack (trend + vol veto)

Fixed map: long if `e_forecast≥0.5` and not `e_risk≥0.85`.

| Slice | Sharpe after cost | n_trades | vs B&H total ret |
|-------|-------------------|----------|------------------|
| train | ~1.03 | 78 | underperforms B&H |
| val | ~0.42 | 35 | underperforms B&H |
| **test** | **~-0.002** | 43 | underperforms B&H |

`exploratory_hard_gates_pass`: **false** (test Sharpe, overfit gap).

**Knowledge gain:** Layered architecture works end-to-end; this particular thin map is **not** an edge. Vol skill ≠ trade edge when mapped with naive mom long.

## LEDA-5a `leda5_xasset` (ETH→BTC Forecast)

| Metric | BTC∩ETH 1d |
|--------|------------|
| pearson eth_mom_lag vs btc_fwd | ~0.00 |
| spearman score vs btc_fwd | ~0.00 |

Cross-asset lagged ETH mom rank shows **no material linear skill** on this operationalisation. Does not justify swapping into the stack yet.

## LEDA-5b B&H + vol veto (`e_risk ≥ 0.85`)

| Slice | Sharpe | excess vs B&H | n_trades | max DD |
|-------|--------|---------------|----------|--------|
| train | ~1.22 | **positive** | 39 | ~0.74 |
| val | ~0.59 | ~0 | 28 | ~0.61 |
| **test** | ~0.12 | **negative** | 16 | ~0.45 |

`exploratory_hard_gates_pass`: **false** (min trades, Sharpe, overfit gap).

**Knowledge gain:** Vol persistence skill does **not** automatically translate to a holdout-valid risk-off policy at this fixed threshold. Train-period improvement is not confirmatory evidence. Do **not** retune threshold on test.

## Next IG priorities

1. Document and stop naive threshold fishing; if revisiting risk policy, pre-register threshold grid on train only with family ledger.
2. Prefer new **information** (different free series / mechanisms) over mom grammar clones.
3. No paid data without EIR; no shadow.
