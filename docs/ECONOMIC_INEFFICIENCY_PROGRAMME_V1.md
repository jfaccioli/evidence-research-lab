# Economic Inefficiency Programme V1

**Authority:** Research Director standing order  
**Opened:** 2026-07-30  
**Suspends (temporary):** Search for immediately deployable strategies from the free admissible shelf  
**Does not weaken:** Pre-registration, trial accounting, confirmatory gates, or deployment dual flags  

## Objective shift

| Before (suspended) | Now |
|--------------------|-----|
| Find another strategy | Identify **economically plausible reasons** BTC might be **temporarily predictable** |
| Assume answer is on free shelf | Discover **smallest additional information** needed for the best remaining inefficiencies |

## Method (mandatory order)

For every proposed inefficiency:

1. **Why** should it exist?  
2. **Who** creates it (which participants)?  
3. **Why** not arbitraged away immediately?  
4. **Which observables** would reveal it?  
5. **Does the lab already have** those observations?  
6. **If not**, what is the **minimum** additional data?  

Only then: score, rank, open study or issue Evidence Investment Review (EIR).

## Scoring (0–5)

| Code | Meaning |
|------|---------|
| **Dur** | Expected durability of the inefficiency |
| **EV** | Expected economic value if real |
| **Obs** | Observability with clean PIT data |
| **DataCost** | Inverse cost of required data (5 = free shelf / free delayed) |
| **Pα** | Expected P(deployable alpha under our gates & envelope) |
| **Overlap** | Overlap with retired families (higher = worse) |

**Inefficiency priority score:**

```text
IScore = 1.4*Dur + 1.3*EV + 1.2*Obs + 1.0*DataCost + 1.6*Pα − 1.3*Overlap
```

## Catalogue location

- Machine: `research_kb/rd/inefficiency_catalogue.json`  
- CLI: `python -m crl rd inefficiencies`  
- EIR (if top blocked): `docs/EVIDENCE_INVESTMENT_REVIEW_INEFFICIENCY_2026-07-30.md`

## Relation to other programmes

| Programme | Role under this initiative |
|-----------|----------------------------|
| Research Director | Owns ranking + EIR |
| Alpha Discovery | Executes only **opened** inefficiency programmes under frozen gates |
| Trading Platform | Idle for alpha; remains engineering |
| Free-shelf residual-vol / mom / inv-vol / basis risk-off | **Not** reopened as strategy search |

## Success

Uncertainty reduction about *whether and why* temporary predictability can exist — including honest “requires data we do not have” and nulls after acquisition.
