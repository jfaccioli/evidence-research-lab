# Mechanism study: uncertainty_behaviour v1

**CLI:** `python -m crl observe study-uncertainty-behaviour`

## Question

How do market participants change behaviour under uncertainty?

## Hypothesis

High lagged RV co-occurs with lower intensity, shifted taker aggression, and wider
absolute cross-venue basis.

## Results

| Property | mean high RV − low RV | Supported? |
|----------|----------------------|------------|
| log intensity | **+0.09** (higher, not lower) | **No** (opposite) |
| taker buy ratio | ~-0.001 | **No** |
| abs basis | ~0 | **No** |
| abs premium | **+** | **Yes** |
| abs funding | **+** | **Yes** |

## Interpretation

Under high RV, **leverage stress proxies are elevated**; **participation intensity is
higher**, not lower (activity concentrates in volatile regimes). Cross-venue abs basis
does not systematically widen with high RV under this definition.

## LEDA

`leda_candidate: false`. No preregistered trading candidate.
