# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`  
**Synthesis:** `docs/PROPERTY_SYNTHESIS_REVIEW_2026-07-29.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| Property shelf | aggression, premium, residual, stable supply, DeFi TVL, **cross-venue basis** |
| Property Synthesis Review | **Done** — composite stress **null** vs rv_lag |
| Composite LEDA programme | **Not opened** (family retired) |
| Shadow | **Not justified** |

## Synthesis decision (locked)

Equal-rank stress family `leda_synth_stress_equal_rank_v1` **retired** for free
recombination. RV lag remains the dominant next-vol baseline (~0.96 IC). Other
properties retain descriptive value by role.

## Queue

| Rank | Object | Status |
|------|--------|--------|
| — | Cross-venue basis | **Characterized** (calendar-day fixed) |
| — | Synthesis review batch | **Done** (composite null) |
| **1** | New **orthogonal** free property *or* pre-reg risk channel only if mechanism-specific claim (not stress average) | **Next** |
| **2** | Conf / shadow | Blocked |

## Commands

```bash
python -m crl observe fetch-cross-basis
python -m crl observe characterize-cross-basis
python -m crl observe synthesis-review
```
