# etf_flow exploratory — complete

**Date:** 2026-07-30
**Status:** **REJECT family** under frozen gates

| Field | Value |
|-------|-------|
| series_id | `us_spot_btc_etf_net_flow_usd_m_farside_v1` |
| source | Farside public all-data table |
| n_events | 654 |
| publish_lag_days | 1 |
| window dataset | `window_etf_flow_ineff_v1_BTCUSDT_1d_09b384293486` |
| content_hash | `faa7bb976e73b6c9…` |

## Results

| Stage | Outcome |
|-------|---------|
| Exploratory | **0/4** passed_val |
| Confirmatory | **not run** (no survivors; confirmatory budget unspent) |

## Decision

Retire `family_etf_flow_ineff_v1`. See `GATE_AUTOPSY_V1.md` and `research_kb/rd/ETF_FLOW_INEFF_V1_FALSIFICATION.json`.

## Attribution

Bitcoin ETF flow table compiled by Farside Investors (https://farside.co.uk/bitcoin-etf-flow-all-data/). Local research pin only.
