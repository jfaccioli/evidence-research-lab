# Research Director (RD) Programme

**Status:** Top-level laboratory programme  
**Package:** `crl.research_director`  
**KB:** `research_kb/rd/`  
**CLI:** `python -m crl rd …`  
**Standing order:** `docs/STANDING_RESEARCH_DIRECTOR_DIRECTIVE.md`

## Purpose

Research Director is **not** an experiment runner.

It is the **principal investigator** of the laboratory: maximise long-term scientific
value and the probability of discovering economically meaningful, reproducible
trading advantages — **without weakening scientific standards**.

## Success metric

Not: number of experiments or properties.

**Increase the laboratory's understanding of how markets function while maximising
the probability of discovering durable, confirmatory-grade trading advantages.**

## Responsibilities

1. Maintain a **global map** of all research programmes.  
2. **Rank** future directions by information gain, economic significance, novelty,
   P(durable alpha), cost, external deps, and overlap with retired work.  
3. **Prevent** duplicate or low-value research.  
4. **Allocate effort** across independent programmes (not a single serial path).  
5. Maintain the **scientific knowledge graph**.  
6. Coordinate **external scientific awareness** (mechanisms, not model cloning).  

## Programme map (top-level)

| Programme | Role |
|-----------|------|
| **Research Director** | Prioritisation, knowledge graph, anti-duplication |
| **Alpha Discovery** | Only path from evidence to production strategies |
| **Mechanism Discovery** | Economic/behavioural mechanisms |
| **LEDA** | Layered evidence decision architecture (science + thin stack) |
| **Trading Platform** | Engineering deploy readiness (benchmarks only until APPROVED) |
| **Ops / Governance** | Readiness, kill switch, dual-flag LIVE, frozen gates |

## Research selection scores (0–5 unless noted)

| Score | Meaning |
|-------|---------|
| **EIG** | Expected information gain about market function |
| **EEV** | Expected economic significance if true |
| **Pα** | Expected probability of durable alpha (under our gates) |
| **SciRisk** | Scientific risk / confounds (higher = riskier; lower better for rank) |
| **EngCost** | Engineering / trial cost (higher = costlier) |
| **ExtDep** | External dependency severity (0=none … 5=paid/key-critical) |
| **Overlap** | Overlap with retired families (higher = more redundant) |

**Composite priority (default):**

```text
score = 1.5*EIG + 1.2*EEV + 1.5*Pα − 0.8*SciRisk − 0.7*EngCost − 0.5*ExtDep − 1.2*Overlap
```

Open programmes only when score is competitive **and** not blocked by retirement.

## Knowledge graph layers

```text
Economic Mechanisms
  → Market Properties
    → Evidence Channels
      → Forecast Targets
        → Decision Policies
```

Each edge stores: rationale, supporting evidence ids, refuting evidence ids, status.

## Interrupt policy

Continue autonomously. Interrupt only for:

- high-value **new programme** open;  
- **external data** scientifically justified;  
- confirmatory **survivor**;  
- **major model contradiction**;  
- strategic decision requiring human judgement.  

## Non-negotiables

- Never weaken gates.  
- Trading Platform ≠ alpha.  
- Alpha Discovery is the only production-strategy path.  
- Nulls retire families permanently unless new data class + new pre-reg.  
