# Pre-registered experiment: leverage_incremental_rv_skill_v1

**CLI:** `python -m crl observe study-leverage-incremental-rv`  
**Result:** **FAMILY RETIRED** (null)

## Question

Does OI-build contain next-RV information **orthogonal to** lagged RV?

## Design (locked before evaluation)

- Residual: expanding OLS `rv_next ~ rv_lag` (min 120)
- Primary: IC(build_flag, residual)
- Threshold: residual IC ≥ 0.05 **and** mean residual | build > not build
- Trial cost: 1

## Results

| Metric | Value |
|--------|--------|
| IC(rv_lag, rv_next) | **0.958** |
| IC(build, rv_next) | 0.186 |
| **IC(build, residual)** | **0.027** |
| mean residual | build | +4e-5 |
| mean residual | not build | -2.8e-4 |

**Decision:** residual IC not material → **retire** `leverage_incremental_rv_skill_v1`.

## Scientific conclusion

Leverage build is a **coarse state correlated with already-elevated RV**. It does
**not** improve next-RV forecast skill beyond pure RV lag under this operationalisation.

This **resolves the contradiction** between leverage_cycle descriptive support and
synthesis stress null: mean differences can appear without incremental forecast value.

**Do not re-open** this family without a new pre-reg **and** new observation class.
