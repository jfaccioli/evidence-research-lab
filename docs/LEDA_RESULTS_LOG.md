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

## LEDA-6 pre-registered vol-veto threshold grid

Thresholds locked: `{0.70, 0.80, 0.90, 0.95}` — **all** reported; family size 4.

| thr | test Sharpe | test excess vs B&H | n_trades | hard pass |
|-----|-------------|--------------------|----------|-----------|
| 0.70 | ~0.41 | ~+0.13 | 18 | **no** (min_trades) |
| 0.80 | ~0.25 | ~-0.02 | 18 | no |
| 0.90 | ~-0.02 | ~-0.25 | 16 | no |
| 0.95 | ~0.26 | ~-0.03 | 14 | no |

**n_pass_exploratory_hard_gates = 0.**  
Do **not** promote thr=0.70 despite positive test excess (under min_trades + multiplicity).

## Next IG priorities

1. Prefer new **information** channels (free series / mechanisms) over more vol-threshold fishing.
2. Optional: paper-path audit wire from `decide_bar` (ops, not alpha).
3. No paid data without EIR; no shadow.
