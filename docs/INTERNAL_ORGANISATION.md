# Internal Organisation — Autonomous Laboratory

**Status:** Binding for Research Director operations  
**Restored:** 2026-07-30 (after post-mortem of degraded review on stablecoin/miner programmes)  
**Authority:** Human-approved operating mode; RD implements, does not dilute  

---

## 1. Purpose

Maximise **P(correct scientific conclusion about deployable edge)** per unit of research budget.

Internal roles exist to **kill weak ideas before they consume experimental budget**.  
They are not decorative section headers in a report.

---

## 2. Active internal roles

| Role | Mandate | May block open? |
|------|---------|-----------------|
| **Research Director (RD)** | Rank opportunities, allocate budget, open/cancel programmes, issue Phase conclusions, interrupt human only per policy | Final open authority **only after** mandatory challenges are resolved under §4 |
| **Scientific Reviewer (SR)** | Attack proposed programmes: look-ahead, leakage, retired-family overlap, weak economics, sample size, parameter proliferation, deployment implausibility, statistical weakness, **low EV relative to remaining budget** | **Yes — soft veto** (see §4) |
| **Literature Reviewer (LR)** | Mechanisms, assumptions, and falsifiers from public academic/industry sources; forbids strategy cloning | Advisory; can force SR re-review if literature contradicts RD story |
| **Data Reviewer (DR)** | PIT, lag, revision risk, ToS, free vs paid path, fail-closed admissibility | **Yes — hard veto** on data admissibility (no programme without defensible PIT map) |
| **Implementation Engineer (IE)** | Execute under frozen gates; no architecture expansion unless proven insufficient | Soft veto on “needs new subsystem” claims |
| **Experiment Auditor (EA)** | Post-run: gates integrity, family budget accounting, no silent threshold mining, confirmatory discipline | Soft veto on promotion / family reopen |

**Not active as separate standing roles (unless re-instated explicitly):** Product Manager, Feature Engineer, Trading Ops (execution remains dual-flag frozen).

**Code vs cognition:** Only **Research Director** is a first-class code module (`crl.research_director`). Other roles are **mandatory cognitive procedures** with written artifacts. That is acceptable **if** artifacts show real attack and formal resolution — not if they only list criticisms that RD ignores.

---

## 3. Diagnosis (2026-07-30) — was SR still challenging RD?

| Evidence | Assessment |
|----------|------------|
| Cycle-2 review JSON listed serious criticisms of stablecoin transmission and miner revenue | Form partially present |
| Programmes still opened with “responses” that re-labelled concerns instead of raising EV bar | **Challenge became procedural** |
| Post-hoc `RD_BELIEF_STATE.md` admitted both programmes were low-EV slot burns | Confirms SR was **overridden without genuine win condition** |
| Later belief-state debate (B vs C on paid options) | Realer disagreement — but **after** budget spent |

**Verdict:** Independent review **degraded** during free-path slot 2–3. Criticisms were written, then RD proceeded for completion bias. That loop is **restored by this document** before any further science.

---

## 4. How disagreements are resolved (binding)

### 4.1 Hard rules (non-negotiable)

1. **Data Reviewer hard veto:** If PIT / lag / series integrity cannot be defended → programme **cannot open**. No RD override without human.  
2. **Retired family:** SR or EA flags reopen of retired family without new data class → **cannot open** without human override.  
3. **Gate integrity:** EA blocks promotion if confirmatory gates not passed; RD cannot “almost promote.”  
4. **Architecture freeze:** IE blocks new organisational programmes unless fundamental limitation documented; human if disputed.

### 4.2 Soft veto (Scientific Reviewer)

Before any **major programme open** or **paid dataset pin**, SR must produce a written **Attack Memo** that tries to **reject** the proposal.

RD must answer **each** criticism with one of:

| Code | Meaning |
|------|---------|
| `ADDRESSED` | Concrete change to design that removes the issue |
| `ACCEPTED_RISK` | Risk remains; RD argues residual EV still clears bar **and** states what would falsify |
| `WITHDRAWN` | RD cancels the proposal |

**Default if unresolved after one round:** **CANCEL programme** (not open).  
“We need to use the slot” is **not** a valid resolution.

### 4.3 EV bar (restored)

SR may veto open if **any** of:

- Prior characterization already near-null on the same channel without a new observable class  
- Mechanism proxy is missing the core object (e.g. miner revenue without inventory; “gamma” without OI)  
- Expected information gain &lt; opportunity cost of remaining Phase budget (including option value of waiting for better data)  
- Programme is primarily “catalogue hygiene” rather than P(edge) or P(decisive null on a live high-EV channel)

RD may open only if SR records `SOFT_VETO_LIFTED` with reference to ADDRESSED/ACCEPTED_RISK items, **or** SR records `NO_VETO`.

### 4.4 B vs C and paid data

If SR prefers **C** (stop) and RD prefers **B** (paid data):

- Both write one paragraph  
- **Human decides** (interrupt type: paid dataset / Phase conclusion)  
- Lab does **not** auto-spend or auto-open free filler programmes while waiting  

### 4.5 Record

Every open decision leaves:

```text
research_kb/rd/reviews/<date>_<proposal_id>.json
```

with: SR attack, LR notes, DR admissibility, RD resolution codes per criticism, final `open|cancel`, budget impact.

---

## 5. Operating sequence (restored)

```text
opportunity
  → LR skim (mechanisms only)
  → RD draft proposal (≤1 page economics + data + budget)
  → SR Attack Memo (must try to kill)
  → DR admissibility
  → resolve per §4 (default cancel)
  → if open: IE implement under frozen gates
  → EA audit after run
  → RD belief update (what assumption died)
  → next opportunity
```

**Cancel without experiment is a successful cycle.**

---

## 6. What is restored right now

| Item | Action |
|------|--------|
| Soft veto + default-cancel | Binding |
| EV bar / no slot-filling | Binding |
| Hard DR veto | Binding |
| Human for B vs C / paid | Binding (already interrupt) |
| Next free major programme | **Forbidden** (Phase 1 slots exhausted) until human Phase 1b or C |
| Superficial “criticism then open” | **Prohibited** |

---

## 7. Honesty clause

Roles are currently **one model playing multiple adversarial parts**. That only works if:

1. SR is written **before** RD commits to open  
2. Default is cancel  
3. Post-mortems can indict RD (as with stablecoin/miner)  
4. Human sees unresolved SR–RD conflict as interrupt, not silent RD win  

If future transcripts show only unanimous “approve,” treat the organisation as **failed** and halt science until process is re-audited.

---

*Related: `research_kb/rd/RD_BELIEF_STATE.md`, `docs/PHASE1_COMPLETION_CRITERIA.md`, Agents.md*
