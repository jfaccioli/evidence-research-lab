# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Architecture:** **LEDA** — `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`  
**Roadmap:** `docs/RESEARCH_ROADMAP_LEDA_V1.md`  
**Results:** `docs/LEDA_RESULTS_LOG.md`  
**Protocol:** `docs/LEDA0_PROTOCOL.md`

## Status

| Stage | Value |
|-------|--------|
| Confirmatory trading candidates | **0** |
| LEDA-0…5b | **Implemented + evaluated** |
| LEDA-4 stack economics | **Fail** exploratory hard gates |
| LEDA-5a xasset IC | **~null** |
| LEDA-5b vol-veto-on-B&H | **Fail** holdout (train tease only) |
| Shadow trading milestone | **Not justified** |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| — | LEDA-0…4 | Scaffold + stack economics | **Done** |
| — | LEDA-5a | ETH→BTC forecast skill | **Done** (null) |
| — | LEDA-5b | B&H + vol veto economics | **Done** (holdout fail) |
| **1** | **LEDA-6** | Pre-registered risk-threshold study **or** free macro/x-series channel (choose by IG, family ledger) | **Next** |
| **2** | Conf | Full pipeline confirmatory | Blocked |

## Commands

```bash
python -m crl leda protocol
python -m crl leda eval-vol-risk
python -m crl leda eval-trend
python -m crl leda eval-xasset
python -m crl leda eval-stack
python -m crl leda eval-vol-veto
python -m crl leda decide --e-forecast 0.7 --e-risk 0.2
```

## Rules

- No free-text LLM promotion path  
- No paid data without EIR  
- No gate softening / no threshold fishing on test  
- Nulls are success when uncertainty falls  
