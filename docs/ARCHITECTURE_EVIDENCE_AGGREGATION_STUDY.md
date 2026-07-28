# Architecture study: indicator discovery vs evidence aggregation

**Date:** 2026-07-28  
**Status:** Research / architecture only — **no implementation in this deliverable**  
**Request:** Assess whether the lab’s decision architecture should evolve from *one hypothesis → one signal → one trade* toward a scientifically validated **probabilistic evidence-aggregation engine**.

Public literature is incomplete evidence. No proprietary firm playbooks are claimed.

---

## 0. Executive conclusion

| Question | Answer |
|----------|--------|
| Is the user’s observation scientifically sound? | **Yes.** Experienced decision-makers and serious quant practice combine **many weak, imperfect information channels**, not single magic indicators. |
| Is V1’s core problem “wrong indicators”? | **Only partly.** The deeper issue is the **decision architecture**: atomistic long/flat rules. |
| Is V2 (new *classes*) still right? | **Directionally yes**, but incomplete if each class still ends as an isolated “programme that trades.” |
| Should we build an “AI Investment Committee” of free-form LLM agents that vote on trades? | **No as primary architecture** — uncalibrated, hard to PIT-test, high overfit/anthropomorphism risk. |
| Should we evolve toward **numeric evidence aggregation** (specialist channels → calibrated scores → frozen decision map)? | **Yes as long-term target architecture (call it EAE / “Committee of Calibrated Evidence”).** |
| Should V2-A proceed **unchanged**? | **No.** |
| Should V2-A proceed **modified**? | **Yes — as the first Evidence Channel (vol/risk), not as a standalone signal→trade product.** |
| Implement V2-A in this turn? | **No.** Architecture + revised roadmap first (per your instruction when a better long-term design emerges). |

**One line:** Keep frozen scientific standards; change the *object we discover* from *trade signals* to *calibrated evidence streams*, then a single testable aggregator.

---

## 1. How successful practice combines information (public)

### 1.1 Discretionary traders (stylised, non-proprietary)

Public descriptions of discretionary process (trading education, interviews, risk books) repeatedly emphasise:

- **Multiple incomplete cues** (structure, trend quality, vol, macro, sentiment, positioning, narrative).  
- **Context / regime**: the same pattern means different things in different states.  
- **Probability and risk**, not certainty: size, pass, or wait when uncertainty is high.  
- **Experience as Bayesian prior**: soft, non-reproducible — the lab **cannot** copy this as code, but can copy the *structure* (many weak inputs + risk filter).

**Takeaway for the lab:** The competitive skill is often **integration under uncertainty**, not isolated indicator edge.

### 1.2 Quantitative firms (public methodology themes)

Documented / textbook quant practice (not secret sauce):

| Theme | Public form |
|-------|-------------|
| **Factor / multi-signal** | Many weak predictors combined with shrinkage, regularisation, or explicit weights |
| **Forecast combination** | Equal weight, stacking, Bayesian model averaging (BMA), dynamic model averaging — combine models, not pick one “winner” forever |
| **Calibration** | Probabilities must match frequencies; miscalibrated “60%” destroys Kelly-style decisions |
| **Separation of concerns** | Alpha forecast vs risk model vs portfolio construction vs execution (classic quant stack) |
| **Multiplicity** | Counting trials; deflated performance; holdout (already lab strengths) |
| **State dependence** | Regime filters; conditional models |

**Takeaway:** Elite *process* looks more like **layered probabilistic decision systems** than like a catalogue of single rules that each “fire a trade.”

### 1.3 What public ML trading papers often get wrong (for us)

Many papers optimise **directional accuracy** or in-sample fit without:

- economic costs,  
- proper PIT,  
- calibration,  
- multiplicity,  
- decision-layer evaluation.

The lab must **not** copy that failure mode into a multi-agent wrapper.

---

## 2. Architecture families — fundamental differences

| Architecture | Core object | Decision | Strength | Failure mode |
|--------------|-------------|----------|----------|--------------|
| **A. Indicator / single-rule** | One boolean feature rule | Long/flat when fires | Simple, auditable | Ignores combination; V1 exhaustion |
| **B. Probabilistic forecasting** | *P(outcome)* or density | Threshold / Kelly / risk map | Aligns with uncertainty | Needs calibration + economic mapping |
| **C. Evidence aggregation** | Vector of **evidence scores** from channels | Aggregator → action | Matches multi-cue reality | Overfit aggregator if free |
| **D. Ensemble / committee of models** | Many models same task | Average / BMA / vote | Robustness to model error | Correlated errors; weight fishing |
| **E. Market state classification** | Discrete state | Policy table per state | Interpretable conditioning | State leakage; too many states |
| **F. Uncertainty-aware decisions** | Forecast + confidence / spread | Trade only if confident | Reduces overtrading | False confidence if miscalibrated |
| **G. Multi-agent LLM “AI committee”** | Natural-language opinions | Vote / debate → trade | Flexible narrative | **Weak science**: non-reproducible, hard PIT, uncalibrated, prompt-overfit |

**Important distinction:**

- **C + B + F** can be made scientifically rigorous.  
- **G without numeric calibration** is theatre unless each agent is forced to output **schema-bound, PIT, hashable evidence** and is scored like any other model.

---

## 3. “AI Investment Committee” — assessment

### 3.1 Attractive idea (keep)

Specialists for Technical structure, Market structure, Macro, Sentiment, Risk, Portfolio, Execution — each contributes **partial evidence**.

That mirrors real organisations and discretionary cognition.

### 3.2 Dangerous implementation (reject as primary)

| Pattern | Problem |
|---------|---------|
| LLM agents free-text “I am bullish” | Not calibrated; not reproducible |
| Agents see future context in prompts | PIT violation |
| Committee vote without holdout of **aggregator** | Extreme overfit |
| Agents invent features post-hoc | Multiplicity explosion |
| “Experience” encoded as prose | Unfalsifiable |

### 3.3 Scientifically acceptable committee (recommend)

Rename for honesty: **Evidence Channel Architecture (ECA)** or **Calibrated Investment Committee**.

```text
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Channel:    │  │ Channel:    │  │ Channel:    │
│ Vol / Risk  │  │ Trend / TA  │  │ Macro       │  ...
│ evidence e1 │  │ evidence e2 │  │ evidence e3 │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │  each e_i ∈ [0,1] or score + CI, PIT, versioned
       └───────────┬────────────────────┘
                   ▼
         ┌─────────────────────┐
         │ Aggregator A(e)     │  frozen map or trained once on train only
         │ → p_hat or utility  │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │ Decision policy π   │  long/flat/size; costs; risk envelope
         └─────────────────────┘
                    ▼
              frozen gates on π outcomes
```

**Specialist “agents”** may be:

- pure code modules (preferred), or  
- LLM-assisted *feature proposal* offline only (never live decision without freeze).

Each channel must publish:

| Field | Requirement |
|-------|-------------|
| `evidence_id` | Stable name + version |
| `score` | Numeric in fixed scale (e.g. [0,1] “risk-on support”) |
| `asof_time` | PIT timestamp |
| `inputs_hash` | What data was used |
| `calibration_report` | On validation only; not test |

---

## 4. Scientific testability, PIT, overfit resistance

### 4.1 How to test an aggregation architecture

| Layer | Test |
|-------|------|
| **Channel alone** | Does `e_i` forecast *its claimed target* (e.g. vol, not forced into trade)? Calibration, skill scores |
| **Aggregator** | On train/val only: does A(e) improve decision utility vs baselines? **One-shot confirmatory** on holdout |
| **Decision policy** | Full economic path: costs, min trades, WF — **same frozen gates** as today |
| **Ablation** | Remove one channel; does OOS degrade? (guards correlated junk) |
| **Multiplicity** | Each channel version + aggregator version counts as trials in family ledger |

### 4.2 PIT rules

- Every channel may only use data with `event_time ≤ bar close`.  
- Aggregator may only use channel scores asof bar close.  
- No agent transcript may include future bars, future series, or post-outcome narratives.

### 4.3 Overfit resistance (stronger than V1 if done right)

| Control | Role |
|---------|------|
| Freeze channel list before looking at aggregator OOS | Pre-registration |
| Shrinkage / equal weight first | Avoid weight fishing |
| Calibration on val only | Prevent test peeking |
| Ablation requirement | Prefer independent evidence |
| Cap channels early (2–4) | Multiplicity |
| Null channel allowed | Honest “no view” |

**Equal-weight average of weak calibrated scores** is often more robust than optimised weights (forecast combination literature).

### 4.4 What remains fail-closed

Promotion still requires confirmatory survival of the **full decision policy π**, not “pretty committee debate.”

---

## 5. Comparison to current V2 roadmap

| V2 element | Relation to evidence aggregation |
|------------|----------------------------------|
| V2-A Vol forecast → risk policy | **Natural first channel**: uncertainty / risk evidence |
| V2-B Cross-asset transfer | Second channel: relative / lead-lag evidence |
| V2-C Conditional trend | Third channel: structure/trend evidence *inside state* |
| V2-D Risk-as-edge | Overlaps decision policy π (risk layer), not a “signal” |
| V2 as isolated programmes each promoting trades | **Insufficient** — recreates atomism at class level |

**Gap in V2 as written:** each programme still optimises toward a standalone trading rule.  
**Fix:** reframe V2 programmes as **Evidence Channel builds**, with an explicit later stage **Aggregator + Decision Policy** once ≥2 channels exist.

---

## 6. Recommendation

### 6.1 Long-term architecture

**Adopt as strategic target:**

**Evidence Channel Architecture (ECA)** — a scientifically testable “investment committee” of **calibrated numeric evidence streams**, not free-form AI debate.

Phases:

| Phase | Name | Deliverable |
|-------|------|-------------|
| **ECA-0** | Standards | Channel schema, PIT, calibration protocol, aggregator pre-reg rules |
| **ECA-1** | First channel | Vol/risk evidence (modified V2-A) |
| **ECA-2** | Second channel | Cross-asset or conditional trend (modified V2-B/C) |
| **ECA-3** | Aggregator v0 | Equal-weight or pre-reg logistic on train only → π long/flat |
| **ECA-4** | Confirmatory | Full stack under frozen economic gates |
| Later | More channels | Macro, flows — only if they emit calibrated evidence |

### 6.2 What to do with V2-A specifically

| Option | Decision |
|--------|----------|
| Proceed **unchanged** (another signal→trade programme) | **No** |
| **Cancel** vol work | **No** — highest free EV *channel* |
| **Modify** into first Evidence Channel + risk evidence scores | **Yes** |
| **Implement now** | **No** — this study forbids implementation until architecture is accepted; next step is roadmap lock then implement |

### 6.3 Why not jump straight to multi-agent LLM committee

Because without channels that are **individually falsifiable and calibrated**, aggregation amplifies noise and destroys reproducibility — the opposite of this lab’s mission.

### 6.4 Why this is higher EV than more V1/V2 atomistic programmes

Atomistic programmes already failed across many **information classes** that would have been committee “seats.” The missing piece is **how evidence becomes a decision**, not only **what series we use**.

---

## 7. Risks of the recommended architecture

| Risk | Mitigation |
|------|------------|
| Aggregator overfit | Equal weight first; one-shot conf; freeze channel list |
| Correlated channels | Ablation; diversity requirement |
| Scope creep / multi-year rewrite | Thin ECA-0 schema; build one channel at a time |
| LLM agent theatre | Ban free-text voting for promotion |
| “Always trading” culture | Explicit null: flat when aggregate confidence low |

---

## 8. Revised research roadmap (proposal)

See **`docs/RESEARCH_ROADMAP_ECA_V2.md`** (Evidence Channel Architecture).

---

## 9. Final answer to the core question

> Should the lab transition from searching for individual predictive signals to building a scientifically validated probabilistic decision engine that accumulates many independent pieces of evidence?

**Yes — as the long-term scientific architecture.**  

> Should V2-A proceed unchanged?

**No.**  

> Should we implement V2-A immediately?

**Not in this deliverable.** First lock the ECA roadmap; then implement **modified V2-A as Evidence Channel #1 (vol/risk)**.

That ordering maximises the chance that the next code we write builds the **right object** (evidence), not another lonely indicator.
