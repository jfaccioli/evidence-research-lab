# Programme: Stablecoin exchange netflow → BTC (v1)

**Status:** Locked exploratory  
**Mechanism:** Net stablecoin flow onto/off exchanges as risk-on dry-powder proxy for BTC spot long-only rules.

Distinct from BTC coin netflow (Q1): object is **USD-stable liquidity**, not BTC inventory.

## Series (binding)

| Field | Value |
|-------|-------|
| Source | Free CMD `stablecoin_exchange_netflow.json` (CC BY 4.0) |
| series_id | `cmd_stablecoin_exchange_netflow_v1` |
| publish_lag_days | 1 |
| Features | prefix `sc_` via external series |

## Hyps ≤5

`examples/batch/stablecoin_flow/`. Do not expand without v2.

## Attribution

Crypto market data provided by Crypto Market Data by Ercin Dedeoglu.
