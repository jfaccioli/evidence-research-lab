# Living research queue

**Updated:** 2026-07-30  
**Architecture:** **Frozen**  
**Phase 1 stop rules:** `docs/PHASE1_COMPLETION_CRITERIA.md`

## Phase 1 budget (summary)

| Cap | Value |
|-----|--------|
| Calendar | → **2026-10-28** (90 days) |
| Major inefficiency programmes | **3** (1 completed null: ETF flow) |
| External datasets | **2** (1 used: Farside ETF) |
| Confirmatory-class evals | **10** (2 PCS; ETF used 0 conf) |
| Parallel science programmes | **1** |

Must end with **A** / **B** / **C**.

## Completed science

1. **PROGRAMME_ETF_FLOW_INEFF_V1** — **REJECT family** (0/4 exploratory; PIT-ok Farside lag-1 aggregate)

## Active work (sequential)

1. Open **next ranked inefficiency** that fits remaining budget (≤2 programme slots left; 1 dataset slot left)  
2. Or if none can run without new data: EIR path or move toward Phase 1 conclusion  
3. Issue Phase 1 conclusion when budget forces it — no infinite “next mechanism”

```bash
python -m crl rd phase1
python -m crl rd eir
python -m crl rd inefficiencies
```

## Do not

- New organisational programmes  
- Reopen ETF flow / retired families without new data class + human override  
- Optimise for experiment count  
