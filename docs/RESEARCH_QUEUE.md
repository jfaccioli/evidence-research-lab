# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`  
**Inventory:** `docs/OBSERVATION_INVENTORY.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| Bottleneck | Market **property** coverage / quality |
| Characterized free properties | `kline_aggression`, `perp_premium`, `premium_residual` |
| LEDA promotion | **Refused** for all three |
| Residual finding | Linear next-RV skill **collinear with funding** (residual IC ~0) |
| Shadow | **Not justified** |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | `kline_aggression` | Spot kline microstructure | **Characterized** |
| — | `perp_premium` | Futures mark–index premium | **Characterized** |
| — | `premium_residual` | Expanding residual vs funding | **Characterized** (linear next-RV null) |
| **1** | Next free property | Prefer **new mechanism** (e.g. aggregate stable supply) over more funding/premium transforms | **Next** |
| **2** | Joint risk state design | Only as descriptive multi-property map after pre-reg — not promotion | Optional |
| **3** | Conf / shadow | Blocked | Blocked |

## Commands

```bash
python -m crl observe inventory
python -m crl observe characterize-aggression
python -m crl observe fetch-premium
python -m crl observe characterize-premium
```

## Rules

- Properties first; characterization before LEDA  
- Understanding without edge is success  
- Frozen gates; no paid data without EIR  
