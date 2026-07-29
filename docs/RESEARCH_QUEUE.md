# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Architecture:** **LEDA** — `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`  
**Results:** `docs/LEDA_RESULTS_LOG.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory candidates | **0** |
| LEDA-0…6 | **Implemented + evaluated** |
| Vol-veto grid (4 thr) | **0 hard-gate passes** |
| Shadow | **Not justified** |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | LEDA-0…6 | Contracts → skill → stack → xasset → vol grid | **Done** |
| **1** | **LEDA-7** | Paper-path audit wire (`decide_bar` → paper session log) **or** free non-OHLCV channel if IG > ops | **Next** |
| **2** | Conf | Frozen-gate confirmatory | Blocked |

## Commands

```bash
python -m crl leda protocol
python -m crl leda eval-vol-risk | eval-trend | eval-xasset
python -m crl leda eval-stack | eval-vol-veto | eval-vol-veto-grid
python -m crl leda decide --e-forecast 0.7 --e-risk 0.2
```

## Rules

- No LLM promotion path; no paid data without EIR; no gate softening  
- No threshold fishing after LEDA-6  
