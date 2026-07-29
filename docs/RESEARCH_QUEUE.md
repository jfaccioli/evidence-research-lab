# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| Mission | Scientific discovery of market properties |
| LEDA promotions from properties | **0** |
| Shadow | **Not justified** |

## Characterized free properties

| Property | Role finding | LEDA |
|----------|--------------|------|
| kline_aggression | participation; intensity↔next RV | no |
| perp_premium | leverage stress; collinear with funding for linear next-RV | no |
| premium_residual | linear next-RV **null** after funding | no |
| stablecoin_agg_supply | liquidity stock; dlog30↔next RV ~0.29 | no |
| **defi_agg_tvl** | DeFi capital lock; **null** linear BTC next-RV/direction | no |

## Queue

| Rank | Object | Status |
|------|--------|--------|
| **1** | Next free property with new mechanism (blocked paths: CoinGecko mcap history 401) | **Next** |
| **2** | Optional multi-property independence matrix write-up (science, not architecture) | Optional |
| **3** | Conf / shadow | Blocked |

## Commands

```bash
python -m crl observe fetch-stable-supply && python -m crl observe characterize-stable-supply
python -m crl observe fetch-defi-tvl && python -m crl observe characterize-defi-tvl
```
