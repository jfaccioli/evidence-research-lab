# Market property inventory

**Updated:** 2026-07-29  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`  
**Terminology:** *market properties* (not indicators, not signals)

## Characterized free properties

| Property | Measures | Independence | Primary role | LEDA? |
|----------|----------|--------------|--------------|-------|
| **kline_aggression** | Taker buy share; trade count | tbr↔ret ~0.36; intensity↔RV | participation / activity | No (char only) |
| **perp_premium** | Mark–index premium (perps) | ~0.68 vs funding; ~0 vs ret | uncertainty / leverage stress | No (char only) |

Details: `PROPERTY_PERP_PREMIUM_V1.md`, `OBSERVATION_KLINE_AGGRESSION_V1.md`.

## Already known / exhausted as atomistic trade grammar

OHLCV path, volume filters, funding prints, OI, free CMD on-chain family, PM panel, FRED macro, LEDA mom+vol maps.

## Blind spots still open (free first)

| Property | Mechanism | Notes |
|----------|-----------|-------|
| premium residual after funding | Leverage stress orthogonal to funding print | Natural next characterization |
| stablecoin aggregate supply growth | Crypto liquidity stock | DefiLlama-class; verify PIT |
| cross-venue spot dislocation | Venue inventory pressure | Multi-API effort |
| options skew / IV | Tail insurance | Often paid |

## Low EV (do not re-mine)

More SMA/mom clones; more free CMD inventory clones; vol-threshold fishing beyond LEDA-6.
