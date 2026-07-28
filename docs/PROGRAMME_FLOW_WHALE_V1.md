# Programme: Exchange flow / large-player positioning (v1)

**Status:** **Scaffolded** (PIT join + mock + 8 locked hyps). **No real flow science batch until versioned real history is ingested.**  
**Related closeout:** `docs/PHASE2_CLOSEOUT.md`  
**Deferred sketch:** superseded for design detail by this file; old DEFERRED doc remains historical pointer.

## Scientific question

> Do point-in-time **net exchange flow** (or large-transfer) features support pre-registered long-only / flat rules under frozen gates — or is “follow flow/whales” a null under honest lag?

## Join / lag (binding)

1. Observation known only at `flow_time` (UTC publish/availability time).  
2. As-of: last `flow_time ≤ bar close`.  
3. Signal → **next open** (lab default).  
4. Missing flow → NaN → rule false.

## Features (causal)

`flow_last`, `flow_chg_1`, `flow_into_exch`, `flow_off_exch`, `flow_high`/`flow_low`, `flow_z_60`, `flow_inflow_extreme`, `flow_outflow_extreme`.

## Pre-registered hyps (≤8)

See `examples/batch/flow/`. **Do not expand without new programme version.**

## Data

| Path | Role |
|------|------|
| Mock | `sources/flow_mock.py` — tests only |
| Real | Future: versioned parquet under `data/processed/flow/` with hash; paid or free APIs only with human OK |

**Mock results are never promotion evidence.**

## Non-goals

- Live Telegram whale bots without PIT  
- Leverage / copy-trading perps  
- Gate softening  

## Execution when real data lands

1. Ingest + hash real series.  
2. `crl batch` / `run-programme` with `flow_events=…` on temp registry.  
3. Autopsy + thesis; confirmatory only if earned.
