# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`  
**Inventory:** `docs/OBSERVATION_INVENTORY.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| Mission | Scientific discovery of market properties |
| Characterized free properties | aggression, premium, premium residual, **stablecoin supply** |
| LEDA promotions | **0** (all refused pending stronger pre-reg claims) |
| Shadow | **Not justified** |

## Characterized properties (summary)

| Property | Role | Key independence | LEDA |
|----------|------|------------------|------|
| kline_aggression | participation | intensity ↔ next RV | no |
| perp_premium | leverage stress | ~0.68 vs funding | no |
| premium_residual | collinearity check | linear next-RV **null** after funding | no |
| stablecoin_agg_supply | liquidity stock | dlog30 ↔ next RV ~0.29; ~0 vs ret | no |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | Properties above | Characterized | **Done** |
| **1** | Next new mechanism | Prefer properties **orthogonal** to OHLCV+funding+premium+stable stock | **Next** |
| **2** | Optional pre-reg | Joint risk-state description (not trade) if science warrants | Optional |
| **3** | Conf / shadow | Blocked | Blocked |

## Commands

```bash
python -m crl observe inventory
python -m crl observe characterize-aggression
python -m crl observe fetch-premium && python -m crl observe characterize-premium
python -m crl observe characterize-premium-residual
python -m crl observe fetch-stable-supply && python -m crl observe characterize-stable-supply
```

## Rules

- Market properties first; characterization before LEDA  
- Understanding without edge is success  
- No architecture churn; frozen gates; no paid data without EIR  
