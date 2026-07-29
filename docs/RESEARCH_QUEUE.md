# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`  
**Inventory:** `docs/OBSERVATION_INVENTORY.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| Bottleneck | Market **property** coverage / quality |
| Characterized free properties | `kline_aggression`, `perp_premium` |
| LEDA promotion of either | **Refused** (characterization only) |
| Shadow | **Not justified** |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | `kline_aggression` | Spot kline microstructure | **Characterized** |
| — | `perp_premium` | Futures mark–index premium | **Characterized** |
| **1** | **`premium_residual`** | Premium after residualizing funding (independence science) | **Next** |
| **2** | Optional free property | Stablecoin supply growth if PIT-clean | Pending |
| **3** | Pre-reg LEDA risk/state | Only if residual informative | Blocked on science |
| **4** | Conf / shadow | Blocked | Blocked |

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
