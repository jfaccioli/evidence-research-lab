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
| Real | `data/processed/flow/<series_id>.parquet` columns `flow_time`, `net_flow` |
| Loader | `crl.shared.data.sources.flow_ingest.resolve_flow_series` — **fail-closed** if missing |

**Mock results are never promotion evidence.**

Sign convention: **positive net_flow = net into exchanges**.

## Non-goals

- Live Telegram whale bots without PIT  
- Leverage / copy-trading perps  
- Gate softening  
- Silent fallback to mock in science batches  

## Execution when real data lands

1. Human places versioned parquet under `data/processed/flow/<series_id>.parquet` (or OK paid API ingest).  
2. `resolve_flow_series(series_id)` → events + content hash.  
3. `crl batch` / pipeline with `flow_events=` / `flow_series_id=` on **temp registry**.  
4. Autopsy + thesis; confirmatory only if earned.
