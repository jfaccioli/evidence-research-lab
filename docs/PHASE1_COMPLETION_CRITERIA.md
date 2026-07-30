# Phase 1 Completion Criteria

**Effective:** 2026-07-30  
**Status:** Binding for Research Director and Alpha Discovery  
**Architecture:** Frozen (no new organisational programmes unless a fundamental limitation is found)

## Why this exists

The laboratory can always invent “the next mechanism.”  
Phase 1 must **end** with a scientifically meaningful conclusion—not indefinite activity.

## Phase 1 question

Under our constraints (BTC-first, long/flat, no leverage, realistic costs and lag, frozen gates),  
is there a **sufficiently robust, confirmatory-grade edge**—or not?

## Maximum research budget (Phase 1)

| Budget | Cap | Counted as |
|--------|-----|------------|
| **Major inefficiency programmes** | **3** total | ETF create/redeem (slot 1); at most **2** further pre-reg programmes after that |
| **External datasets acquired** | **2** free-or-paid pins | e.g. ETF flows = 1; second only if EIR ranks higher than stop |
| **Paid data spend** | **Human-approved only**; default **$0** until EIR + human OK | Subscriptions discouraged; prefer one-time export |
| **Calendar time** | **90 days** from 2026-07-30 (ends **2026-10-28**) | Wall-clock; extensions only by human |
| **Confirmatory-class trial budget** | **≤ 10** confirmatory (or PCS-style one-shot test) evaluations | Exploratory hyps within a locked programme ≤ **4** per programme |
| **Parallel exploratory programmes** | **1** active science programme at a time | Reserve may be named; not executed in parallel |

Machine state: `research_kb/rd/phase1_budget.json`

## Sequential roadmap (no new boxes)

```text
1. Pin ETF flow series (free delayed preferred) — if blocked, EIR already issued
2. PROGRAMME_ETF_FLOW_INEFF_V1 (pre-reg → exploratory ≤4 → at most 1 confirmatory)
3. If null: open next ranked inefficiency that fits remaining budget
4. If null again: open at most one more (budget cap)
5. Issue Phase 1 conclusion (mandatory)
```

Do **not** reopen retired families (daily mom, stress composites, residual-vol skill, PCS vol-scale, PCS basis risk-off, free CMD conf-null clones) without new data class **and** human override.

## Phase 1 must end with exactly one conclusion

### Conclusion A — Deployable candidate path  
A strategy (or risk policy) **passed confirmatory** under frozen gates and is eligible for **live-data shadow** under existing dual-track rules.

### Conclusion B — Richer data justified  
All budgeted programmes that could run on free/paid-within-budget data null’d, **and** the RD EIR still ranks a **specific** paid dataset with EV > remaining free options.  
Human decides whether to fund Phase 1b (data) or stop.

### Conclusion C — Unlikely robust edge under current constraints  
Budget exhausted (or remaining budget cannot change the answer), no confirmatory survivor, and no EIR that clearly justifies further spend.  

**Wording for C (default if quiet nulls):**  
> Under Phase 1 constraints (BTC spot, long/flat, no leverage, daily/4h admissible data we could obtain within budget), we did **not** find a confirmatory-grade edge. Public/free-style daily prediction under our gates is **unlikely** to contain a sufficiently robust, deployable advantage without a **qualitatively richer** information class or a **material change** of mandate (horizon, assets, shorting, leverage—which we still forbid unless human reopens).

## What does *not* count as Phase 1 success

- More architecture or RD subsystems  
- More property characterisation without a pre-reg deployable decision  
- Attractive exploratory backtests that fail confirmatory  
- Benchmark platform metrics  

## After Phase 1

| If | Then |
|----|------|
| **A** | Shadow → (if pass) micro-live package; capital scale still human-only |
| **B** | Human funds data **or** chooses **C** / pause |
| **C** | Freeze alpha search; optional productise research OS; personal trading remains off |

## Research Director duties under this doc

1. Refuse new programmes that exceed budget or reopen retired families.  
2. Keep **one** active science programme.  
3. After each programme: update `phase1_budget.json` counters and thesis/roadmap.  
4. When any budget line is hit **or** calendar ends: **force** conclusion A/B/C within 7 days.  
5. Do not invent “next mechanism” as a way to avoid concluding.

## Relation to ETF EIR

`docs/EVIDENCE_INVESTMENT_REVIEW_INEFFICIENCY_2026-07-30.md` remains the acquisition path for programme 1.  
If free ETF data cannot be pinned within **14 days** of this document (by 2026-08-13), RD must either:

- document free-path failure and request human paid export (still within dataset cap), **or**  
- skip to next inefficiency that fits remaining budget, **or**  
- if none, move toward conclusion **C**.

---

*Architecture frozen. Phase 1 has a stop rule.*
