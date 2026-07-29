# Research Roadmap — LEDA (Layered Evidence Decision Architecture)

**Version:** LEDA-V1  
**Date:** 2026-07-29  
**Basis:** `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`  
**Supersedes as default framing:** standalone ECA aggregator-only sketch (ECA ideas retained as **channels**)

## Layers (frozen responsibilities)

| # | Layer | Responsibility | Thin default (current mandate) |
|---|--------|----------------|--------------------------------|
| 1 | **Forecast** | Probabilities / expected edge + uncertainty | `leda2_trend` scores; **no** size/orders |
| 2 | **Risk** | Vol, DD, regime, model trust; **veto/trust** | `leda1_vol_risk`; veto long |
| 3 | **Portfolio** | Size, caps, diversification | 0/1 long-only + existing envelope |
| 4 | **Execution** | When/how; costs; modes | next_open; paper/shadow/live dual-flag |

## Evidence channels

Specialist modules emit numeric PIT evidence into Forecast and/or Risk.  
Not free-text AI votes.

## Build order

| Step | Name | Notes |
|------|------|-------|
| **LEDA-0** | Contracts + schema | **Done** — `crl.leda` types/protocol |
| **LEDA-1** | Risk channel (vol) | **Done** — skill eval only |
| **LEDA-2** | Forecast channel | **Done** — `leda2_trend`; skill eval only |
| **LEDA-3** | Portfolio map + Execution wire | **Done** — `stack.decide_bar` |
| **LEDA-4** | Full-stack exploratory economics | **Done** — fail exploratory hard gates |
| **LEDA-5a** | ETH→BTC forecast | **Done** — IC ~null |
| **LEDA-5b** | B&H + vol veto | **Done** — holdout fail (train tease) |
| **LEDA-6** | Next IG channel or pre-reg risk study | **Next** |

## Non-goals

- Mean-variance multi-strategy optimizer before ≥2 APPROVED  
- Smart order routing  
- LLM committee promotion path  
- Gate softening  
- Shadow/live from exploratory L4 alone  

## Standards

Unchanged: explor/conf, costs, min_trades, PIT, no leverage, family trial ledger.
