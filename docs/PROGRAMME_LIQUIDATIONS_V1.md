# Programme: Long liquidations forced-flow (v1)

**Status:** Locked exploratory  
**Mechanism:** Elevated perpetual **long liquidations** as forced selling / stress; long-only rules that go flat or skip risk-on, or rebound after extreme stress.

Distinct from OI/funding v1 locks (stock of leverage vs **forced unwind intensity**).

## Series

| Field | Value |
|-------|-------|
| Source | CMD `btc_long_liquidations.json` (CC BY 4.0) |
| series_id | `cmd_btc_long_liquidations_v1` |
| publish_lag_days | 1 |
| Features | prefix `liq_` |

## Hyps ≤5

`examples/batch/liquidations/`.
