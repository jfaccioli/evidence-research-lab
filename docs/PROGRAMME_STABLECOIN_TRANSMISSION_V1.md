# PROGRAMME_STABLECOIN_TRANSMISSION_V1

**Status:** **COMPLETE — REJECT family** (exploratory 0/4)  
**Inefficiency:** `ineff_stablecoin_transmission`  
**Internal review:** OPEN_WITH_CONDITIONS (`research_kb/rd/INTERNAL_REVIEW_2026-07-30_CYCLE2.json`)

## Question

Does **lagged system-wide stablecoin supply growth** (mint/burn proxy) contain incremental deployable information for BTC spot long/flat under frozen gates?

## Distinct from

- CMD **exchange** stablecoin netflow family (already exploratory null)
- Property characterization (descriptive only; this is gated pre-reg)

## Data

| Field | Value |
|-------|--------|
| series | `defillama_stablecoin_supply_dlog_lag1_v1` |
| value | Δlog(aggregate peggedUSD supply) at lag-1 event_time |
| derived_from | existing DefiLlama stock pin (not a new paid acquisition) |
| prefix | `scg` |

## Budget

≤4 exploratory; ≤1 confirmatory; family `family_stablecoin_transmission_v1`
