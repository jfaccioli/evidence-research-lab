# Research Roadmap — LEDA (Layered Evidence Decision Architecture)

**Version:** LEDA-V1  
**Date:** 2026-07-29  
**Basis:** `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`  
**Supersedes as default framing:** standalone ECA aggregator-only sketch (ECA ideas retained as **channels**)

## Layers (frozen responsibilities)

| # | Layer | Responsibility | Thin default (current mandate) |
|---|--------|----------------|--------------------------------|
| 1 | **Forecast** | Probabilities / expected edge + uncertainty | Calibrated scores; **no** size/orders |
| 2 | **Risk** | Vol, DD, regime, model trust; **veto/trust** | Vol/risk evidence; veto long |
| 3 | **Portfolio** | Size, caps, diversification | 0/1 long-only + existing envelope |
| 4 | **Execution** | When/how; costs; modes | next_open; paper/shadow/live dual-flag |

## Evidence channels

Specialist modules emit numeric PIT evidence into Forecast and/or Risk.  
Not free-text AI votes.

## Build order

| Step | Name | Notes |
|------|------|-------|
| **LEDA-0** | Contracts + schema | Docs + thin types; evaluation per layer |
| **LEDA-1** | Risk channel (vol) | Modified V2-A / ECA-1 |
| **LEDA-2** | Forecast channel | Trend or cross-asset |
| **LEDA-3** | Portfolio map + Execution wire | Minimal; reuse paper path |
| **LEDA-4** | Full-stack confirmatory | Frozen economic gates |

## Non-goals

- Mean-variance multi-strategy optimizer before ≥2 APPROVED  
- Smart order routing  
- LLM committee promotion path  
- Gate softening  

## Standards

Unchanged: explor/conf, costs, min_trades, PIT, no leverage, family trial ledger.
