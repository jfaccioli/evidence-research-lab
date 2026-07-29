# Mechanism study: leverage_cycle v1

**CLI:** `python -m crl observe study-leverage-cycle`  
**Not a trading programme.**

## Question

How does leverage **build** and **unwind**?

## Hypothesis

Leverage *build* (rising OI + elevated |funding| or premium) precedes higher next-RV
than leverage *unwind* (falling OI).

## Results (BTC 1d + Bybit OI + funding/premium)

| State | n | mean rv_next | p(high rv_next) | mean fwd_ret |
|-------|---|--------------|-----------------|--------------|
| **build** | 179 | **0.0349** | 0.51 | ~0 |
| **unwind** | 435 | 0.0291 | 0.37 | ~0 |
| quiet | 1567 | 0.0267 | 0.25 | ~0 |
| unconditional | 2181 | 0.0278 | 0.29 | ~0 |

**build − unwind mean rv_next ≈ +0.0057** → hypothesis **supported** under pre-reg margin.

## Interpretation

Leverage **build vs unwind** is a useful **state description** for uncertainty
(next-RV). Directional mean returns remain ~null.

## LEDA / promotion

| Flag | Value |
|------|--------|
| `leda_candidate` | **false** |
| `preregistered_candidate` | **false** |

Support of a descriptive mechanism claim is **not** automatic LEDA entry. A future
risk-state channel would need a **new pre-reg** (e.g. “OI-build state raises next-RV
forecast skill beyond RV lag alone”) with family trial cost and ablations.
