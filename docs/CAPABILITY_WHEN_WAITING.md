# Research capability while waiting for new data

**Updated:** 2026-07-28  
**Policy:** Do not spend wait-time on low-EV free BTC technical clones. Improve **time-to-evidence** when a new series lands.

## Goal

Minimise friction:

```text
new parquet / series lands
  → series ready check
  → locked programme (INDEX.yaml)
  → explor + confirmatory (same attach)
  → autopsy + queue record
  → (if candidates) paper clock path
```

## Tooling (implemented)

| Command | Purpose |
|---------|---------|
| `crl series list` | Inventory `data/processed/flow` + `external` |
| `crl series ready --hyp-dir examples/batch/flow` | Series attach checklist (≥180 events) |
| `crl run-programme examples/batch/flow` | Auto-attach series from INDEX + conf on pass |
| `crl run-programme … --require-series` | Fail closed if series missing/short |
| `crl new-programme my_slug --kind external --series-id …` | Scaffold lock dir + design |
| `crl queue` | Machine queue state JSON |

## INDEX.yaml external block

```yaml
external:
  kind: flow          # or external
  series_id: my_series_v1
  prefix: xser        # external feature prefix only
  publish_lag_days: 1
dataset:
  symbol: BTCUSDT
  interval: 1d
  window_from_series: false  # true for short alt series
```

## Dropping a new series (operator)

1. Place `data/processed/external/<series_id>.parquet` with `event_time`, `value`  
   (or flow: `flow_time`, `net_flow` under `data/processed/flow/`).  
2. Optional `.meta.json` with content hash notes.  
3. Point programme INDEX `series_id` at it.  
4. `crl series ready --hyp-dir …` then `crl run-programme … --require-series`.

## Explicit non-work while waiting

- Another free CMD long-only technical filter programme  
- Governance theatre  
- LIVE adapter without APPROVED survivors  
