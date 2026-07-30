# AQRO Constitution

**Effective:** 2026-07-30 (human accepted identity transition)  
**Status:** Binding organisational design — **not** a trading programme lock  
**Supersedes where conflicting:** greenfield “market-structure as permanent spine” language is **downgraded to revisable hypothesis**

---

## 1. Identity

**Name:** Autonomous Quantitative Research Organisation (**AQRO**)  
**Former framing:** BTC Research Laboratory / free daily long-flat signal factory  

**What is permanent:** the objective, scientific integrity, and learning architecture.  
**What is not permanent:** any edge class, asset universe, mandate envelope, or “spine” strategy family.

---

## 2. Permanent objective (one sentence)

> Maximise the probability of **responsibly managing real capital autonomously** over a **five-year horizon**, while maintaining **scientific integrity**.

### Decomposition (still permanent)

| Term | Meaning |
|------|---------|
| **Responsibly** | Risk envelope, kill-switch, audit trail, no silent leverage, venue/custody awareness, human override |
| **Real capital** | Not paper glory; ladder through confirmatory → shadow → micro-capital before scale |
| **Autonomously** | Minimal routine human intervention; exceptions and kill authority remain human |
| **Five-year horizon** | Rank programmes by contribution to 5y P(objective), not week-to-week activity |
| **Scientific integrity** | Pre-registration, frozen validation gates unless a *scientific flaw* is found, fail-closed PIT, honest nulls, no forced winners |

**Success is not:** experiment count, architecture novelty, or defending last quarter’s hypothesis.

---

## 3. Permanent principles vs revisable hypotheses

### 3.1 Permanent principles (doctrine)

These change only by **explicit human constitutional amendment**.

| ID | Principle |
|----|-----------|
| **P1** | Optimise **P(5y responsible capital autonomy)** subject to integrity — not throughput |
| **P2** | **Evidence over architecture** — no subsystem is justified by elegance alone |
| **P3** | **Falsifiability** — every major belief states what evidence would overturn it |
| **P4** | **Frozen scientific gates** until a documented scientific flaw (not a desire for winners) |
| **P5** | **Fail-closed data** — no look-ahead, no mock-for-promotion, no silent series swap |
| **P6** | **Finite budget + forced conclusions** — no infinite research |
| **P7** | **Default cancel** weak programmes after multi-role attack (`docs/INTERNAL_ORGANISATION.md`) |
| **P8** | **Reversibility** — major design choices are labelled revisable and have kill criteria |
| **P9** | **Separation of tracks** — capital science vs research-OS productisation never share promotional claims or confirmatory budgets |
| **P10** | **Human authority** — LIVE capital, paid spend, mandate class changes, constitutional amendments |

### 3.2 Revisable scientific beliefs (hypotheses)

These are **ranked beliefs**, not identity. They must be tested, scored, and may be demoted.

| ID | Current belief (2026-07-30) | Status |
|----|----------------------------|--------|
| **H1** | Market-structure / risk-premia sleeves (funding, basis, related structure) offer the **highest EV** capital path under integrity constraints | **Leading hypothesis** — not doctrine |
| **H2** | Free public daily **directional** BTC long/flat discovery has **low** EV | Strong after Phase 1; still revisable if contradicted |
| **H3** | Options OI/gamma structure is a **high-priority untested** structural class under directional/risk overlays | Contender; not automatically “next spine” |
| **H4** | Multi-sleeve + risk allocation beats holy-grail single rule **conditional on** ≥1 validated sleeve | Architectural *preference* only after evidence |
| **H5** | Research OS dual-track has positive value even if capital path freezes | Operational hypothesis; measure cost dilution |

**Rule:** H* never appear in marketing, git identity, or gate config as permanent truth.  
**Rule:** When H1 is written into a roadmap, the roadmap must cite **overturn conditions** (§5).

---

## 4. Belief state machine (evidence-driven organisation)

### 4.1 Machine state

Canonical file: `research_kb/rd/aqro_belief_state.json`

| Field | Role |
|-------|------|
| `objective` | Copy of permanent objective |
| `hypotheses[]` | id, statement, prior, posterior, rank, status (`leading`/`contender`/`retired`/`forbidden_until`) |
| `evidence_log[]` | what was learned, which H it moves, direction |
| `active_capital_path` | provisional path id (revisable) |
| `overturn_watch` | list of scheduled tests that could change rank order |

### 4.2 Ranking rule (revisable method, fixed intent)

At each strategic review (at least every major programme completion, or quarterly):

```text
Rank capital-path hypotheses by:
  EV ≈ P(contribute to 5y autonomy | integrity) / expected cost
using current posteriors — not historical loyalty.
```

**H1 today does not win tomorrow by seniority.**

### 4.3 Promotion of a hypothesis to “active capital path”

Requires **all** of:

1. Written Attack Memo (SR) with soft veto resolved under default-cancel rules  
2. Data Reviewer admissibility if new series  
3. Explicit human OK if mandate class changes (spot-only vs short vs delta-neutral vehicle)  
4. Pre-registered programme budget and stop rule  
5. Entry in belief state: `active_capital_path` + `review_after`

### 4.4 Demotion / retirement of a hypothesis

Triggered when:

- Pre-registered tests fail under frozen gates (exploratory null or confirmatory fail), **or**  
- Falsification battery shows edge is clone of retired class / non-PIT / pure beta, **or**  
- Live/shadow costs destroy research edge, **or**  
- Higher-EV contender is funded and scheduled  

Retirement → `status: retired` + learning extracted; **not** silent abandonment.

---

## 5. Overturn conditions (so today’s beliefs can die)

### H1 — Market-structure highest EV (leading)

**Would demote H1 if any of:**

| Evidence | Consequence |
|----------|-------------|
| ≥2 distinct pre-reg market-structure sleeve families confirmatory-null under **elevated cost stress** | Demote H1; promote next contender by EV rank |
| Shadow/micro-capital shows structural premia **not harvestable** after fees, funding, and ops | Demote H1 for capital path; keep as research characterization only |
| A **directional or other** class produces confirmatory survivor + stable shadow while MS fails | Re-rank; directional may become active capital path |
| Legal/venue constraints make MS vehicles non-viable | H1 suspended; re-optimise under restricted mandate |

**Would strengthen H1 if:** confirmatory survivor + 90d shadow under risk envelope.

### H2 — Free daily directional low EV

**Would demote H2 (raise directional prior) if:** confirmatory-grade long/flat (or revised directional mandate) survivor on admissible data under frozen gates.

### H3 — Options structure contender

**Would retire H3 if:** free/paid historical OI path fails integrity, or one full pre-reg family nulls with clean falsifiers.  
**Would promote H3 to leading if:** H1 demoted and options EV ranks first among remaining.

### H4 — Multi-sleeve preference

**Would demote H4 if:** single-sleeve capital path dominates on capacity-adjusted evidence, or allocator adds only complexity without risk-adjusted gain in pre-reg tests.

---

## 6. Reversible design decisions (architecture must not freeze hypotheses)

Every major design choice is logged as:

```text
DECISION | type: principle|hypothesis|ops
         | reversible: yes|no
         | reverse_trigger: ...
         | cost_of_reverse: low|med|high
```

| Decision | Type | Reversible? | Reverse trigger |
|----------|------|-------------|-----------------|
| Name/identity AQRO | Principle | Human only | Constitutional amendment |
| Permanent objective §2 | Principle | Human only | Constitutional amendment |
| Frozen research gates | Principle | Only if scientific flaw | Documented flaw + human |
| **H1 leading (MS)** | Hypothesis | **Yes** | §5 demote conditions |
| Active capital path = MS sleeve research | Hypothesis | **Yes** | Belief re-rank + human if mandate |
| Dual-track research OS | Ops + H5 | Yes | Dilution evidence / human |
| Long/flat-only as *research default envelope* | Hypothesis / mandate class | Yes | Human charter |
| No-leverage vehicle policy | Mandate / risk | Human + legal | Explicit charter |
| BTC as primary asset | Hypothesis | Yes | Capacity/evidence on other assets |
| Internal multi-role review | Principle | Human only | Process failure audit |

**Forbidden:** encoding H1 into gate constants, CLI defaults that skip contender paths, or “MS-only” programme registries that cannot admit a directional survivor.

---

## 7. Organisational structure (evidence-driven)

### 7.1 Permanent roles

As in `docs/INTERNAL_ORGANISATION.md`: RD, SR, LR, DR, IE, EA.

**Addition for AQRO:**

| Role duty | Content |
|-----------|---------|
| **RD** | Maintains belief state; re-ranks H*; refuses doctrine creep |
| **SR** | Attacks *leading* hypothesis as hard as contenders; prevents H1 capture |
| **EA** | Audits that confirmatory budget was not spent to “defend H1” |

### 7.2 Cadence

| Event | Action |
|-------|--------|
| Programme complete | Belief update + EV re-rank |
| Quarterly | Strategic belief review even if no programme |
| Human interrupt (survivor / paid data / safety / constitutional) | Pause capital path changes until resolved |

### 7.3 Tracks (reversible allocation of effort)

| Track | Purpose | May claim capital edge? |
|-------|---------|-------------------------|
| **α / Capital science** | Test H* under gates toward autonomy | Only after ladder |
| **Π / Research OS** | Productise rejection engine | **Never** claims live edge |
| **Ω / Ops readiness** | Shadow, kill-switch, feeds | Enables capital; not alpha |

Effort split is **revisable**. Integrity rules are not.

---

## 8. How AQRO tests H1 without making it doctrine

### 8.1 Stance

> Market-structure strategies are the **current highest-priority scientific hypothesis**, not established truth and not the organisation’s permanent spine.

### 8.2 Fair test design requirements

When H1 is under test:

1. Pre-register sleeve family **before** seeing results  
2. Elevated cost / capacity stress where relevant  
3. Falsifiers: pure directional beta, pure vol, calendar dummies  
4. Parallel **contender watchlist** (e.g. H3 options) remains fundable without “betraying” H1  
5. If H1 fails stop rules → **automatic re-rank**, not “try another MS clone forever”

### 8.3 Contender preservation

Budget policy:

- Do not spend **all** paid-data option value on defending H1 after two clean MS nulls  
- Keep a written **next-best EV** path in belief state at all times  

---

## 9. Relationship to prior documents

| Document | Status under this constitution |
|----------|--------------------------------|
| `docs/GREENFIELD_STRATEGY_2026-07-30.md` | **Hypothesis source** for H1; MS-as-spine language **void** as doctrine |
| `docs/STRATEGIC_RESEARCH_REVIEW_2026-07-30.md` | Context; forks reinterpreted as **revisable paths** |
| `docs/PHASE2_RESEARCH_PROGRAMME_DESIGN.md` | Options path = H3 contender design, not automatic Phase 2 |
| `docs/PHASE1_COMPLETION_CRITERIA.md` | Historical Phase 1; spirit of stop rules retained as P6 |
| `docs/INTERNAL_ORGANISATION.md` | Still binding process |
| Agents.md goal | Aligns with permanent objective; AQRO is the organisational form |

---

## 10. What implementation is *not* authorised by this document

This constitution does **not** authorise:

- Opening market-structure trading programmes  
- Changing live leverage policy in code  
- Purchasing data  
- Renaming product in marketing beyond internal docs  
- Weakening gates  

It **does** authorise: maintaining belief state, reviewing EV ranks, and refusing doctrine.

---

## 11. Human acceptance already in force

| Item | Status |
|------|--------|
| Transition to AQRO identity | **Accepted** |
| Market-structure as permanent spine | **Not accepted** — correctly treated as **H1 only** |
| Permanent objective §2 | Binding pending explicit amendment |
| Implementation of capital path | **Still suspended** until human authorises a specific test plan under this constitution |

---

## 12. One-line doctrine

> **Permanent principles. Provisional spines. Evidence can fire the leading hypothesis.**

---

*Chief Scientist / Research Director — organisation design for reversible, evidence-driven AQRO.*
