# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Architecture lock (proposal):** **LEDA** — `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`  
**Roadmap:** `docs/RESEARCH_ROADMAP_LEDA_V1.md`  
**Prior:** ECA study retained; atomistic V1/V2 signal→trade retired as default

## Critical path

| Stage | Status |
|-------|--------|
| Lab ops | Ready |
| Confirmatory survivors | **0** |
| Decision architecture | **LEDA proposed** (Forecast / Risk / Portfolio / Execution) |
| Implementation | **Blocked until LEDA review accepted** (this cycle: review only) |

## Queue

| Rank | ID | Object | Status |
|------|-----|--------|--------|
| **0** | LEDA review | Four-layer vs single decision / ECA | **Done (docs)** |
| **1** | **LEDA-0** | Layer contracts + evidence schema | **Next code** (after proceed) |
| **2** | **LEDA-1** | Risk layer — vol/risk evidence channel | After LEDA-0 |
| **3** | **LEDA-2** | Forecast layer — second channel | After LEDA-1 |
| **4** | **LEDA-3** | Thin portfolio map + execution wire | After ≥1 F + R |
| **5** | **LEDA-4** | Full-stack frozen-gate test | After LEDA-3 |

**Do not:** implement standalone V2-A trade signal; pay for data before free LEDA channels; LLM voting committees.

## Success

Trustworthy multi-year stack = **separated scientific claims** + **calibrated evidence** + **frozen gates** — not more indicators.
