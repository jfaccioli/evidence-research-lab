# Mechanism study: vol_clustering v1

**CLI:** `python -m crl observe study-vol-clustering`  
**Registry:** `docs/MECHANISM_REGISTRY.md`

## Question

What processes cause **volatility clustering**?

## Hypothesis

High-vol states persist partly because **leverage stress** and **liquidity withdrawal**
co-occur with high RV and prolong uncertainty — not only pure statistical RV inertia.

## Minimum observables

| Need | In lab? |
|------|---------|
| RV path | yes |
| Funding / premium | yes |
| Stable supply growth | yes |
| Trade intensity | yes (micro klines) |

## Design (pre-registered)

- High RV: `rv_lag ≥` causal expanding median  
- Persistence: `P(rv_next high | rv_lag high)`  
- Co-factors tested **separately** (no free multi-factor fishing):  
  - abs funding ≥ expanding p75  
  - abs premium ≥ expanding p75  
  - supply dlog30 ≤ expanding p25  
  - log intensity ≤ expanding p25  

## Results (BTC 1d pinned, n≈3246)

| Quantity | Value |
|----------|--------|
| P(high next RV) unconditional | ~0.27 |
| P(high next \| high lag) | ~**0.91** (lift ~3.4×) |
| + abs funding ≥ p75 | ~0.90 (no increase) |
| + abs premium ≥ p75 | ~0.92 (no material increase) |
| + supply dlog30 ≤ p25 | ~0.87 (**lower** persistence) |
| + low intensity ≤ p25 | n=0 with high RV (empty cell) |

**Conclusion:** Under this operationalisation, **cofactors do not increase** high-RV persistence beyond pure RV inertia. Working description of clustering remains **statistical RV persistence**, not leverage/liquidity co-factor prolongation.

This is a **useful null** for the co-factor prolongation claim — not a license for multi-factor stress fishing.

## LEDA

Not opened. `leda_candidate: false`.
