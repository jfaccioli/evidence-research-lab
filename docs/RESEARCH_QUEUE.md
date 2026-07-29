# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Philosophy:** `docs/OBSERVATION_DISCOVERY_DIRECTIVE.md`  
**Inventory:** `docs/OBSERVATION_INVENTORY.md`  
**LEDA results:** `docs/LEDA_RESULTS_LOG.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| Primary bottleneck | **Evidence / observation quality** (architecture mature) |
| New observation family | **`kline_aggression`** — characterized |
| Shadow | **Not justified** |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | LEDA-0…7 | Decision stack scaffold | **Done** |
| — | Observation philosophy | Directive + inventory | **Done** |
| — | `kline_aggression` | Characterize taker/intensity | **Done** (see OBSERVATION_KLINE_AGGRESSION_V1) |
| **1** | **`perp_premium`** | Acquire free premiumIndex klines; characterize (not signals) | **Next** |
| **2** | Optional | Intensity residual as LEDA risk *state* channel — only if pre-reg claim locked | Pending |
| **3** | Conf / shadow | Blocked | Blocked |

## Commands

```bash
python -m crl observe inventory
python -m crl observe characterize-aggression
python -m crl fetch --interval 1d   # retains micro columns
python -m crl leda eval-stack
```

## Rules

- Observations first; no indicator fishing  
- Frozen gates; no paid data without EIR  
- Nulls that reduce blindness are success  
