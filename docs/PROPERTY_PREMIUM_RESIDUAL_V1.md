# Market property: premium_residual_vs_funding v1

**Status:** Characterized — **not** a trading programme  
**Method:** Expanding OLS residual of `premium_lag` on `funding_lag` (past-only β, expand_min=60)  
**CLI:** `python -m crl observe characterize-premium-residual`

## 1. What it measures

The component of lagged perpetual premium **not linearly explained** by lagged
funding rate, under causal expanding coefficients.

## 2. Mechanism

If funding already prices the main leverage transfer, residual premium may capture
slow inventory / mark-index stress. Empirically we test whether that residual
still co-moves with uncertainty.

## 3. Results (BTC 1d, n residual ≈ 2346)

| Association | Value |
|-------------|--------|
| resid → fwd_ret | ~**-0.014** (null direction) |
| resid → rv_next | ~**0.001** (null **linear** next-RV) |
| raw premium → rv_next | ~**0.17** |
| funding → rv_next | ~**0.11** |
| resid vs funding_lag | ~0.18 (imperfect residualization OOS) |
| |resid| ≥ p80 mean rv_next | ~0.035 |
| |resid| < p80 mean rv_next | ~0.027 |

## 4. Scientific reading

- The **linear** association of premium with next RV is largely **shared with funding**.  
- After causal residualization, **linear next-RV skill disappears**.  
- High absolute residual still co-occurs with higher next RV (nonlinear / state
  description) — similar pattern to raw |premium|.  
- Residual is nearly independent of ret_lag and rv_lag.

## 5. Understanding without edge

Yes: clarifies that premium’s linear uncertainty co-movement is not orthogonal
to funding. Prevents double-counting in future risk designs.

## 6. LEDA

`leda_candidate: false`. Do **not** open a residual channel on linear next-RV claim.  
Any future risk map should treat premium and funding as **joint state**, not two
independent edges.
