# Final architectural review: layered decision stack vs ECA

**Date:** 2026-07-29  
**Status:** Architecture only — **no implementation in this deliverable**  
**Question:** Should the lab explicitly separate Forecast / Risk / Portfolio / Execution rather than treating trading as a single decision?

Builds on: `docs/ARCHITECTURE_EVIDENCE_AGGREGATION_STUDY.md`, `docs/RESEARCH_ROADMAP_ECA_V2.md`.

---

## 0. Executive conclusion

| Question | Answer |
|----------|--------|
| Is single-decision trading scientifically ideal long-term? | **No.** |
| Should Forecast / Risk / Portfolio / Execution be **explicit** layers? | **Yes** — this is the simplest *enduring* architecture used in serious quant practice. |
| Does current ECA already capture this? | **Partially** (channels + aggregator + π + ops) but **muddles** forecast vs risk vs sizing vs execution. |
| Redesign ECA? | **Yes — lightly:** rename/clarify into a **Layered Evidence Decision Architecture (LEDA)**. |
| Build full portfolio optimizer / HFT execution now? | **No** — layers can be **thin** under a long-only unit mandate. |
| Increase sophistication for its own sake? | **No** — four *interfaces*, minimal *implementations*. |
| Begin ECA-0/ECA-1 code this turn? | **No** — review first; implementation only after this document is the lock. |

**One line:** Separate *what we believe*, *whether we may act*, *how much*, and *how we act* — with frozen interfaces — while keeping each layer as thin as the mandate allows.

---

## 1. Why separation is the default in serious quant systems

Public textbook / industry process (not proprietary alpha):

| Layer | Responsibility | Typical scientific claim |
|-------|----------------|--------------------------|
| **Forecast** | Expected return / *P(up)* / densities | Predictive skill + **calibration** |
| **Risk** | Vol, DD, liquidity, regime, model trust | Risk forecast skill; **veto** validity |
| **Portfolio** | Size, diversification, constraints | Allocation under constraints (mean-variance, risk parity, simple caps, …) |
| **Execution** | Timing, venue, slippage, ops modes | Cost model; fill integrity |

This separation is older and more boring than multi-agent AI committees — and that is a feature.

Discretionary traders who “combine many weak signals” still implicitly do something similar: narrative/forecast, gut risk check, size, then when/how to enter.

---

## 2. Does explicit layering improve the criteria you named?

| Criterion | Single blended decision | Explicit four layers |
|-----------|-------------------------|----------------------|
| **Scientific validity** | One joint hypothesis; hard to falsify *why* it failed | Each layer has a **distinct falsifiable claim** |
| **Reproducibility** | One opaque rule stack | Versioned contracts between layers |
| **Modularity** | Replace signal ⇒ rewrite trade logic | Swap forecast without rewriting paper broker |
| **Explainability** | “Rule fired” | “Forecast bullish; risk vetoed; size 0” |
| **Calibration** | Often ignored | Forecast cal ≠ risk cal; force both |
| **Overfit resistance** | Sizing/feature fishing conflated | Cannot “fix” size on test if portfolio frozen; cannot retune forecast after risk rules set |

**Judgement:** Explicit layers **improve** all six **if** interfaces stay thin. They **hurt** if each layer becomes a research playground (portfolio ML, execution RL, etc.).

---

## 3. Risks of introducing layers

| Risk | Mitigation |
|------|------------|
| Premature portfolio theory for 1 asset | Portfolio layer = **unit long-only + risk envelope** until ≥2 APPROVED strategies |
| Empty abstraction (code with no science) | Layers are **contracts + evaluation protocols** first; heavy math later |
| Double counting evidence | Channels declare whether they feed Forecast, Risk, or both |
| More moving parts → more bugs | Reuse existing paper/shadow/risk_envelope as Execution/Portfolio stubs |
| Delay forever redesigning | Cap: ECA-0 becomes **LEDA-0** schema; then first channel |

---

## 4. Does current ECA already suffice?

Current ECA sketch:

```text
Evidence channels → Aggregator A(e) → Decision policy π → Ops (paper/shadow/live)
```

| Concept | Already in ECA? | Gap |
|---------|-----------------|-----|
| Multiple evidence streams | Yes (channels) | — |
| Forecast | Partially (if channels emit edge) | Not separated from risk |
| Risk | Partially (e_risk channel idea) | Not a first-class **veto/trust** layer |
| Portfolio | Implicit in π | Not named; easy to smuggle size into “alpha” |
| Execution | Ops path exists | Not named as scientific contract |

**Verdict:** ECA is the right *spirit* (calibrated evidence, not chat votes) but **under-specifies** the classic four-way split. Adding explicit layers is **not** unnecessary complexity for a multi-year system; it is the **minimal clean factoring** of decisions the lab will face when it ever has more than one idea.

**Unnecessary complexity would be:** multi-strategy optimizers, smart order routers, or LLM debate before we have one calibrated forecast and one risk veto.

---

## 5. Redesign: Layered Evidence Decision Architecture (LEDA)

Rename for clarity (ECA ⊆ LEDA):

```text
                    ┌──────────────────────┐
                    │  Evidence Channels   │  (specialists; numeric; PIT)
                    │  e_tech, e_macro, …  │
                    └──────────┬───────────┘
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
   │ 1. FORECAST   │   │ 2. RISK       │   │ (optional    │
   │  layer F      │   │  layer R      │   │  raw channel │
   │  p_hat, μ_hat │   │  trust, veto, │   │  diagnostics)│
   │  uncertainty  │   │  vol/DD/liq   │   │              │
   │  NO trade     │   │  NO size      │   │              │
   └───────┬───────┘   └───────┬───────┘   └──────────────┘
           │                   │
           └─────────┬─────────┘
                     ▼
            ┌────────────────┐
            │ 3. PORTFOLIO   │
            │  layer P       │
            │  size, caps,   │
            │  diversification│
            └────────┬───────┘
                     ▼
            ┌────────────────┐
            │ 4. EXECUTION   │
            │  layer X       │
            │  next_open,    │
            │  costs, modes  │
            └────────────────┘
```

### 5.1 Layer contracts (scientific)

| Layer | **Must** | **Must not** |
|-------|----------|--------------|
| **Forecast F** | Emit calibrated predictive objects for a pre-reg target (e.g. *P(r>0)*, E[r], or density summary) | Choose position size; place orders; silently drop trades for “risk” |
| **Risk R** | Emit trust/veto/risk state from PIT risk features + model confidence | Override forecast labels; invent alpha |
| **Portfolio P** | Map (F, R) → target exposure under **frozen** constraints | Peek at test; retune on confirmatory |
| **Execution X** | Realize P under mode (paper/shadow/live), costs, kill switch | Change economic thesis |

### 5.2 Mandate-thin defaults (simplicity)

For current personal mandate (spot long-only, max position 1, tiny notional):

| Layer | Minimal honest implementation |
|-------|-------------------------------|
| Forecast | One or more channels → `p_hat` or expected edge score |
| Risk | `veto ∈ {0,1}` or continuous `risk_score`; vol forecast channel is **primarily R**, not F |
| Portfolio | `size = 0 or 1` (or continuous later); envelope from existing `RiskEnvelope` |
| Execution | Already: next-open, paper/shadow, dual-flag LIVE stub, cost model in gates |

**No** mean-variance engine required until multiple APPROVED strategies exist.

### 5.3 How evidence channels feed layers

| Channel type | Primary sink | Example |
|--------------|--------------|---------|
| Directional / transfer | **Forecast** | Cross-asset lead-lag score → p_hat |
| Vol / stress / confidence | **Risk** | High forecast RV → veto or risk_score↑ |
| Macro stress | **Risk** (and/or Forecast) | Pre-reg; declare sink |
| Sentiment | Forecast or Risk | Pre-reg |

Atomistic V1 rules mixed all of this into one boolean. LEDA **forbids** that mixing at the scientific claim level.

### 5.4 Scientific validation by layer

| Layer | Evaluation (still fail-closed) |
|-------|--------------------------------|
| Forecast | Calibration (reliability curves), skill (Brier/log-loss/MAE on target), **not** Sharpe alone |
| Risk | Hit rate of vetoes on large adverse moves; false veto cost; vol forecast skill |
| Portfolio | Path metrics under frozen constraints; compare to “always follow F ignoring R” |
| Execution | Slippage/cost model integrity; mode safety (LIVE dual flags) |
| **Full stack** | Existing **economic gates** on final paper path (promotion bar) |

Promotion to APPROVED remains on **full-stack economic outcomes**, after layers are frozen.

### 5.5 Overfitting discipline (layered)

1. Freeze Forecast channel set before fitting Portfolio.  
2. Freeze Risk rules before looking at confirmatory stack Sharpe.  
3. Prefer **pre-reg** Portfolio map (e.g. long iff p_hat > 0.55 and not vetoed) over optimised weights.  
4. Family trial ledger counts: each channel version + each layer map version.  
5. Ablation: stack without Risk vs with Risk — must be interpretable.

---

## 6. Comparison to “AI Investment Committee”

| | Free-text multi-agent vote | LEDA layers |
|--|---------------------------|-------------|
| Roles | Soft personas | Hard scientific contracts |
| Output | Prose | Numbers + PIT hashes |
| Risk | Hidden in debate | Explicit Risk layer |
| Size | Hidden in “conviction” | Portfolio layer |
| Execution | Mixed with opinion | Execution layer only |
| Test | Weak | Layer-wise + full stack |

LEDA **is** the scientifically valid committee: seats are **layers and channels**, not chatbots.

---

## 7. Mapping prior roadmaps

| Prior | Fate under LEDA |
|-------|-----------------|
| V1 signal→trade | Retired |
| V2 hypothesis classes | Become **channels** feeding F or R |
| ECA channels + aggregator | Aggregator splits into **F combine** + **R combine** + **P map** |
| ECA-1 vol channel | **Risk layer input** (primary), not a directional forecast |
| Paper/shadow/live | **Execution layer** (already largely built) |
| Risk envelope / kill switch | Portfolio + Execution (already largely built) |

---

## 8. Simplest multi-year architecture (final lock proposal)

**Name:** Layered Evidence Decision Architecture (**LEDA**)

**Principles:**

1. Four layers with frozen interfaces (Forecast, Risk, Portfolio, Execution).  
2. Evidence channels feed F and/or R with calibrated numeric outputs.  
3. Thin Portfolio/Execution until multi-strategy needs arise.  
4. Same frozen economic gates for promotion of the **stack**.  
5. No free-text voting as promotion evidence.  
6. Build one channel at a time; no empty mega-framework.

**Implementation sequence (after this review is accepted):**

| Step | Deliverable | Complexity |
|------|-------------|------------|
| **LEDA-0** | Layer contracts + evidence record schema + evaluation checklist (docs + thin types) | Low |
| **LEDA-1** | Risk channel: vol/risk evidence (ex-V2-A / ECA-1) | Medium |
| **LEDA-2** | Forecast channel: one directional or cross-asset evidence stream | Medium |
| **LEDA-3** | Minimal Portfolio map + wire Execution (existing paper path) | Low–medium |
| **LEDA-4** | Full-stack explor/conf under frozen gates | Medium |

---

## 9. Direct answers to your six improvement criteria

| Criterion | Explicit layers help? | How |
|-----------|----------------------|-----|
| Scientific validity | **Yes** | Separate claims |
| Reproducibility | **Yes** | Interface versions |
| Modularity | **Yes** | Replace F without rewriting X |
| Explainability | **Yes** | Layered audit trail |
| Calibration | **Yes** | F vs R metrics |
| Overfit resistance | **Yes if thin** | Frozen maps; no joint fishing |

**Would layers add unnecessary complexity?**  
Only if we over-build Portfolio/Execution. **Named thin layers do not** — they prevent years of conflated experiments.

---

## 10. Final recommendation

1. **Adopt LEDA** (four explicit layers + evidence channels).  
2. **Do not** implement a heavy portfolio optimizer or multi-agent chat.  
3. **Do not** implement LEDA-1 until LEDA-0 contracts exist.  
4. **Rescope** former V2-A/ECA-1 as **Risk-layer vol evidence**, not a trade signal.  
5. **Implementation begins only after** this review is treated as locked (your next “proceed” or standing autonomy if already granted for architecture-approved work).

**This turn:** review only — **no code.**

---

## 11. One-sentence architecture

**The simplest long-lived trustworthy system is not a smarter indicator — it is a small, explicit factory where forecasts, risk trust, capital limits, and execution are separate scientific contracts, fed by calibrated evidence, and only jointly promoted under frozen gates.**
