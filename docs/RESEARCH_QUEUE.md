# Living research queue

**Updated:** 2026-07-30  
**Architecture:** **Frozen**  
**Phase 1 stop rules:** `docs/PHASE1_COMPLETION_CRITERIA.md`

## Phase 1 budget (summary)

| Cap | Value |
|-----|--------|
| Calendar | → **2026-10-28** (90 days) |
| Major inefficiency programmes | **3** |
| External datasets | **2** |
| Confirmatory-class evals | **10** (2 already used by PCS) |
| Parallel science programmes | **1** |
| ETF data pin deadline | **2026-08-13** |

Must end with **A** (candidate path), **B** (richer data), or **C** (unlikely robust edge).

## Active work (sequential)

1. ~~Pin free delayed US spot BTC ETF net flows~~ **DONE** (2026-07-30): `us_spot_btc_etf_net_flow_usd_m_farside_v1` under `data/processed/etf/` (Farside public table, `publish_lag_days=1`)  
2. **Next:** open and run `PROGRAMME_ETF_FLOW_INEFF_V1` only (≤4 exploratory hyps; at most 1 confirmatory)  
3. At most two further programmes if null  
4. Issue Phase 1 conclusion — no infinite “next mechanism”

```bash
python -m crl rd phase1
python -m crl rd eir
python -m crl rd status
```

## Do not

- New organisational programmes  
- Reopen retired families without new data class + human override  
- Optimise for experiment count  
