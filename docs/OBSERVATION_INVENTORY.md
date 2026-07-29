# Market property inventory

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`

## Characterized free properties

| Property | Measures | Independence | Primary role | LEDA |
|----------|----------|--------------|--------------|------|
| kline_aggression | Taker share; trade count | tbr↔ret ~0.36 | participation | no |
| perp_premium | Mark–index premium | ~0.68 vs funding | leverage stress | no |
| premium_residual | Premium ⊥ funding | linear next-RV null | collinearity science | no |
| **stablecoin_agg_supply** | Aggregate stable supply growth | ~0 vs ret; ~0.29 dlog30↔next RV | liquidity / uncertainty | no |
| **defi_agg_tvl** | DeFi capital locked | ~0.20 vs stable growth; null BTC linear skill | capital allocation | no |

## Blind spots still open (free first)

| Property | Mechanism | Notes |
|----------|-----------|-------|
| BTC dominance / total mcap share | Relative capital allocation | CoinGecko history **401** without key — blocked free |
| Cross-venue spot basis | Venue inventory pressure | Multi-API |
| ETF flow | Institutional pipe | EIR if paid |

## Low EV (do not re-mine)

SMA/mom clones; CMD netflow clones; premium/funding residual fishing; vol-threshold grids beyond LEDA-6.
