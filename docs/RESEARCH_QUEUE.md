# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Architecture:** **LEDA**  
**Results:** `docs/LEDA_RESULTS_LOG.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| LEDA-0…7 | **Implemented** |
| Economic maps (L4–L6) | **No hard-gate pass** |
| Paper wire (L7) | **Works** (ops only; not edge) |
| Shadow | **Not justified** |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | LEDA-0…7 | Full thin stack + skill + economics + paper audit | **Done** |
| **1** | **Science** | New free evidence channel with higher IG than mom/vol-threshold fishing | **Next** |
| **2** | Conf | Frozen-gate confirmatory | Blocked |
| **3** | Shadow | Only after confirmatory earn | Blocked |

## Commands

```bash
python -m crl leda protocol
python -m crl leda eval-vol-risk
python -m crl leda eval-trend
python -m crl leda eval-xasset
python -m crl leda eval-stack
python -m crl leda eval-vol-veto
python -m crl leda eval-vol-veto-grid
python -m crl leda paper
python -m crl leda decide --e-forecast 0.7 --e-risk 0.2
```

## Rules

- No LLM promotion; no paid data without EIR; no gate softening  
- No further vol-threshold fishing without new pre-reg science case  
- Nulls = success when uncertainty falls  
