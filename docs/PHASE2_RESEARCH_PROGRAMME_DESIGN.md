# Phase 2 Research Programme — Strategic Design

**Status:** Design only — **not authorised for implementation**  
**Date:** 2026-07-30  
**Predecessor:** Phase 1 free path complete → conclusion **B** (`B_richer_data_justified`)  
**Mission (unchanged):** Maximise probability of a **genuine, reproducible, deployable** autonomous BTC trading system under **scientific integrity** (frozen gates; no forced winners)  
**This document does not open Phase 2.** Implementation resumes only after human acceptance of a recommendation below.

---

## 0. Executive consensus (read first)

After multi-role challenge of all major paths, the organisation converges on:

### Recommended Phase 2 shape: **“One paid structure test → binary stop”** (Path **B+**, with dual-track product option)

| Element | Decision |
|---------|----------|
| **Primary science** | Single paid acquisition: historical **Deribit BTC options OI (strike×expiry)** ± greeks/IV, PIT-lagged → one pre-registered programme family ≤4 exploratory / ≤1 confirmatory |
| **If survivor** | Shadow under existing dual-track rules; micro-live still human-gated |
| **If null** | **Hard stop** on alpha search under current mandate → formal **C**; no second paid dataset without a new full EIR + human |
| **Not in Phase 2 science** | Free OHLCV clone grids; ETF flow variants; free netflow reopens; miner/stablecoin reopens; architecture redesign |
| **Parallel (optional, non-science)** | Light **productisation of the research OS** (docs, demos, reliability) — does **not** consume confirmatory budget or claim alpha |
| **Mandate change** (short/leverage/delta-neutral carry) | **Deferred** as a separate **Phase 3 charter** only if (i) options path nulls **and** (ii) human explicitly wants non-long/flat economics — not smuggled into Phase 2 |
| **Probability language** | Subjective, order-of-magnitude; used for ranking, not for false precision |

**Why this wins on EV:** Highest remaining untested structural channel compatible with long/flat; free path already falsified for public daily prediction; process fixes (default-cancel, one-shot paid, hard stop) prevent infinite research.

---

## 1. Phase 1 facts that constrain Phase 2

| Fact | Implication for Phase 2 |
|------|-------------------------|
| Free OHLCV technicals mass-null; PCS vol-scale & basis risk-off rejected | Do not reopen free technical or free-shelf deployable search |
| ETF lag-1 aggregate exploratory null; return→flow ≥ flow→return | Structural demand ≠ daily long/flat edge under our lag/costs |
| Stablecoin Δlog & miner revenue null (and process regret on low EV opens) | Free weak proxies must not fill Phase 2 “to look busy” |
| Confirmatory budget largely unspent (8 left after PCS) | Reserve for true survivors only |
| Architecture mature; research OS valuable even without alpha | Product track is rational **side** objective, not substitute for scientific stop rules |
| Internal review degraded then restored | Phase 2 must bake in SR soft veto, DR hard veto, default-cancel |
| Human interrupt still open on paid data vs C | Phase 2 design is the decision menu, not auto-start |

---

## 2. Challenge every foundational assumption

| Assumption | Challenge | Working conclusion |
|------------|-----------|-------------------|
| **A1.** A deployable autonomous BTC system is still the right primary goal | Lab may already be more valuable as a **rejection engine / research OS**. Forcing alpha search can destroy EV. | Keep alpha as **primary scientific question** only if residual untested channels remain; otherwise pivot product. |
| **A2.** Mandate must stay BTC spot long/flat, no leverage | Many literature edges (funding carry, basis arb, gamma scalping) are **not** long/flat. Staying long/flat maximises integrity of Phase 1 comparison but may **cap P(edge)**. | Phase 2 stays long/flat for the **one** options test. Mandate expansion = separate phase with explicit human charter. |
| **A3.** Options/dealer gamma is the best next bet | Industry GEX is noisy; dealer inventory unobserved; public OI→“dealer” is a **proxy**. Academic crypto options work often studies **hedging effectiveness**, not directional alpha. | Still best **untested** structural class for long/flat; P(success) moderate-low, not high. |
| **A4.** Paid data will unlock edge | Paid data can also **null** honestly — that is success. Risk is paying and then continuing forever. | One-shot purchase + hard stop if null. |
| **A5.** More programmes = more learning | Phase 1 already proved low-EV programmes **destroy** option value. | Phase 2 programme count capped hard (≤1 science family before stop). |
| **A6.** Frozen gates are the bottleneck | Gates killed sparse teases correctly. Softening would invent fake alpha. | Gates stay frozen. |
| **A7.** Daily horizon is required | 4h already partly tested (null-heavy). Intraday needs different costs/capacity and often different data. | Phase 2 options programme may use **daily decision** on lagged structure (not HFT). Intraday only if mechanism demands and data supports. |
| **A8.** We should implement soon | Premature implementation reintroduces completion bias. | **Design complete → human approve → then implement.** |

---

## 3. Strategic paths (full menu)

Estimates are **deliberately coarse** (subjective, for ranking).  
**P(success)** = P(confirmatory-grade candidate under frozen gates within path budget), not P(lifetime wealth).  
**EV** = expected scientific value toward deployable system **or** decisive correct stop (both count).  
**Cost** = money + calendar + confirmatory/trial budget + process risk.

Scale: P and EV on 0–1 rough utility; costs in relative units.

### Path S — Stop alpha (accept C); optional productise research OS

| | |
|--|--|
| **Description** | Declare free+reasonable free-path exhausted; freeze alpha; productise lab as evidence engine |
| **P(deployable system eventually)** | 0.05–0.15 (only if later reopened) |
| **P(correct stop decision)** | **0.55–0.70** under long/flat free constraints |
| **EV (truth)** | High for free-shelf question; medium global |
| **Cost** | Low money; low science risk; opportunity cost of never testing options |
| **Major risks** | Under-exploring true options edge; emotional “we failed” misread of honest nulls |
| **SR stance** | Strongly favours if human will not fund quality options history |

### Path B — Single paid options OI/gamma programme then hard stop

| | |
|--|--|
| **Description** | Buy minimal historical Deribit OI (±greeks); one family; null → C; survivor → shadow ladder |
| **P(confirmatory survivor)** | **0.10–0.25** (honest; proxy risk) |
| **P(decisive learning)** | **0.85–0.95** (null or not, we learn) |
| **EV** | **Highest among science paths** under current mandate |
| **Cost** | Medium money (vendor export; human-set cap); 4–8 weeks calendar; ≤4 expl + ≤1 conf |
| **Major risks** | Non-PIT vendor data; OI≠dealer inventory; GEX folklore; sample regime; overfit expiry dummies |
| **SR stance** | Accept **only** with hard stop after one family and DR PIT pass |

### Path B+ — Path B + parallel non-science productisation

| | |
|--|--|
| **Description** | Same science as B; parallel polish of docs/CLI/demos for research OS commercial option |
| **P(edge)** | Same as B |
| **EV total** | B science EV + product option value |
| **Cost** | B cost + engineering time (must not steal science focus or weaken gates) |
| **Major risks** | Product work dilutes science; marketing claims outrun evidence |
| **SR/IE stance** | OK if product work is **explicitly non-promotional** and budget-split |

### Path M — Mandate expansion (short / flat / long, or funding carry / basis arb)

| | |
|--|--|
| **Description** | Reopen leverage policy or allow delta-neutral; target crypto-carry style edges |
| **P(some edge exists in literature class)** | **0.30–0.50** for funding/basis *as economic phenomenon* |
| **P(deployable under new mandate + gates)** | **0.15–0.35** |
| **EV** | High **if** human accepts mandate change; incomparable to Phase 1 |
| **Cost** | High process (policy rewrite, risk, ops); data maybe free (funding we have) but **scientific reset** |
| **Major risks** | Scope creep; confuses Phase 1 null interpretation; live risk if rushed |
| **SR stance** | **Not Phase 2** — separate charter Phase 3 only after B null or human priority shift |

### Path F — More free structural fishing (new free proxies)

| | |
|--|--|
| **Description** | Another free series / transform programme |
| **P(success)** | **0.02–0.08** |
| **EV** | Low |
| **Cost** | Low money; high opportunity cost |
| **Major risks** | Slot-filling; process regression |
| **SR stance** | **Reject** |

### Path H — Higher frequency / multi-asset free OHLCV

| | |
|--|--|
| **Description** | 1h ETH/alts technical or microstructure without new info class |
| **P(success)** | Low–medium for different claim; **low** if same technical families |
| **EV** | Low under “new claim required” |
| **Cost** | Medium engineering; capacity/friction harder |
| **Major risks** | Clone spam in new clothing |
| **SR stance** | Reject unless **new mechanism + PIT**, not “try ETH mom” |

### Path V — Vendor on-chain / whale / reserves (non-revised PIT)

| | |
|--|--|
| **Description** | Paid true PIT exchange reserves or entity flows |
| **P(success)** | 0.08–0.20 |
| **EV** | Medium-low after free netflow conf-null (overlap) |
| **Cost** | High subscription risk |
| **Major risks** | Paying for same mechanism class already retired |
| **SR/DR stance** | Inferior to options for Phase 2; only if options unavailable |

### Path L — Live forward collection only (no history buy)

| | |
|--|--|
| **Description** | Scrape live Deribit OI daily from now; wait 12–24 months |
| **P(eventual sample adequacy)** | Medium long-run; **near zero** for Phase 2 calendar |
| **EV near-term** | Near zero for deployable system this year |
| **Cost** | Low money; high time |
| **Major risks** | Infinite delay; ToS; missing past regimes |
| **RD stance** | Optional **side** logger; not a Phase 2 primary path |

### Path X — Opaque ML/RL as hypothesis

| | |
|--|--|
| **P(success under Agents.md)** | N/A — **forbidden** as hypothesis form |
| **SR stance** | Reject |

---

## 4. Comparative ranking (truth-oriented)

Score = rough `0.4*P(decisive correct learning) + 0.4*P(path to deployable | mandate) + 0.2*option_value − 0.3*process_risk − 0.2*cost_drag`  
(illustrative; for order, not accounting)

| Rank | Path | Verdict |
|------|------|---------|
| 1 | **B+** (options one-shot + optional product dual-track) | **Recommended** |
| 2 | **B** (options one-shot only) | Acceptable if no product bandwidth |
| 3 | **S** (C + productise) | Recommended **if** human refuses paid data |
| 4 | **M** (mandate expand) | Phase **3** candidate, not Phase 2 |
| 5 | **V** (vendor netflow/reserves) | Dominated by B under current evidence |
| 6 | **L** (forward collect only) | Side project, not Phase 2 core |
| 7 | **H / F / X** | Reject |

---

## 5. Internal multi-role debate (disagreement → resolution)

### Research Director
- Phase 2 is not “more programmes.” It is **one** high-EV structural test or a **clean stop**.  
- Prefers **B+**: options history with hard stop; product track as secondary value capture.  
- Opposes mandate expansion inside Phase 2 (contaminates inference).

### Scientific Reviewer (attack)
- **Against B:** Dealer gamma from public OI is a **proxy stack** (OI → assumed dealer → assumed hedge → spot). Each arrow leaks. Industry GEX is often narrative.  
- **Against endless B-variants:** Without hard stop, B becomes infinite research.  
- **Against F/H:** Completion bias.  
- **For S:** If data quality or price is bad, better C than a bad pin.  
- **Lifts veto on B only if:** (1) DR signs PIT, (2) ≤4 hyps, (3) falsifiers include calendar + RV + mom, (4) null → C mandatory, (5) no second vendor without new EIR.

### Literature Reviewer
- Supports **mechanism existence** of options-linked hedging flows in crypto industry research (GEX/flow-based gamma narratives); academic base thinner for **directional long/flat alpha**.  
- Crypto carry / funding: real economics, wrong mandate fit for Phase 2.  
- ETF: do not re-test daily flow prediction.  
- Extract: test **regime / risk-off / pinning** hypotheses more than “always long when GEX high.”

### Data Reviewer
- Free historical OI: **fail**. Live OI: insufficient sample alone.  
- Purchase must include **snapshot timestamps** or fail-closed.  
- Prefer one-time export; document revision policy.  
- **Hard veto** if vendor cannot state as-of semantics.

### Implementation Engineer
- Lab can attach external series and run gates **without new architecture**.  
- Product dual-track: docs/CLI only; no trading platform redesign as science substitute.  
- Warns against building “GEX engine” before pin.

### Experiment Auditor
- Confirmatory remaining budget is precious; **at most one** confirmatory in Phase 2 science.  
- Sparse high-Sharpe must still die on min_trades.  
- Promotion only to shadow package; no auto micro-live.

### Disagreement product
| Issue | Resolution |
|-------|------------|
| B vs S | **Human chooses** fund quality options history (→ B/B+) or refuse (→ S/C) |
| Proxy quality of GEX | Accepted risk with mandatory falsifiers; not grounds to skip if DR PIT OK |
| Mandate expansion | **Out of Phase 2**; Phase 3 only |
| Product work | Allowed only dual-track, non-promotional |

**Consensus recommendation:** **B+ if funded; S if not funded.** No other Phase 2 science path.

---

## 6. Phase 2 programme design (if human funds Path B/B+)

### 6.1 Objective

> Under frozen gates and long/flat BTC envelope, does **point-in-time lagged Deribit options open-interest / gamma structure** contain incremental, economically usable information for a deployable decision rule — or not?

Success = confirmatory survivor **or** high-quality null that justifies **C**.

### 6.2 Non-objectives

- Beating B&H with clever free OHLCV  
- Building a commercial GEX product as science  
- Multi-vendor data shopping  
- Softening gates  
- NN/RL hypotheses  

### 6.3 Budget (proposed Phase 2 caps)

| Line | Cap |
|------|-----|
| Paid datasets | **1** (options OI/gamma history) |
| Major science programmes | **1** |
| Exploratory hyps (that programme) | **≤ 4** |
| Confirmatory-class evals | **≤ 1** |
| Calendar | **≤ 60 days** from data pin to conclusion |
| Parallel science programmes | **0** (one only) |
| Architecture programmes | **0** unless fundamental limitation |
| Paid USD | **Human-set hard cap** (recommend one-time export; no open subscription without second approval) |

### 6.4 Data specification (binding before buy)

| Field | Requirement |
|-------|-------------|
| Venue | Deribit BTC options |
| Content | OI by strike × expiry × call/put (minimum); greeks/IV optional but valuable |
| Time | Snapshot `asof_time` UTC; documented publish lag |
| History | Prefer ≥ 2 years continuous; document gaps |
| PIT | Decision uses only snapshots with `asof_time + lag ≤ bar decision time` |
| Storage | Versioned parquet + content hash + meta (ToS, vendor, fetch time) |
| Fail closed | Missing lag policy → no programme open |

### 6.5 Pre-registered hypothesis classes (design freeze; exact YAML later)

At most **four**, drawn from distinct economic stories — not four thresholds:

1. **Risk-off under short-gamma / stress positioning** (flat when proxy indicates forced selling regimes)  
2. **Trend participation only outside high positive-gamma pin zones** (avoid long when pinning likely dominates)  
3. **Post-expiry positioning reset** (lagged change in OI structure, not same-day)  
4. **Distance-to-max-OI strike regime** with mild trend filter  

Each must specify: expected direction, decision timestamp, horizon, mapping, rejection conditions.  
**Forbidden:** grid search over strikes, lookback lengths, or GEX formulas after seeing results.

### 6.6 Mandatory falsification battery

- Expiry-calendar dummies alone  
- Realised-vol / vol-regime alone  
- SMA/trend alone  
- Lead-lag: does spot move **before** OI snapshot changes?  
- Extreme days / OPEX-only concentration  
- Winsorize extremes  

### 6.7 Promotion ladder (unchanged philosophy)

```text
exploratory pass → at most one confirmatory
  → candidate → live-data shadow (existing dual-track)
  → micro-live only with explicit human Phase open
```

### 6.8 Stop rules (Phase 2 terminal)

| Outcome | Action |
|---------|--------|
| Confirmatory candidate | Interrupt human: shadow package; do not auto-live |
| Exploratory all fail or confirmatory fail | Issue **C**; freeze alpha under mandate; optional productise |
| Data integrity failure | Fail closed; no silent substitute series; human re-EIR or C |
| Budget/calendar hit | Force B2 conclusion within 7 days (A′ candidate path / C) |

### 6.9 Dual-track product (B+ only)

Allowed **in parallel**, not as science:

- Operator docs, demos of rejection workflow, reliability (`doctor`), narrative of honest nulls  
- Explicit disclaimer: **no live edge claimed**  
- Must not consume confirmatory budget or pressure gate softening  

### 6.10 Governance

- `docs/INTERNAL_ORGANISATION.md` applies: SR Attack Memo before open; DR hard veto; default cancel  
- `docs/PHASE1_COMPLETION_CRITERIA.md` spirit: finite budget, forced conclusion  
- Agents.md: no NN/RL as hypothesis; no gate weaken  

---

## 7. Expected value narrative (honest)

| Scenario | Approx. P | Value |
|----------|-----------|--------|
| Options path → confirmatory survivor | 0.10–0.25 | High (deployable path opens) |
| Options path → clean null | 0.60–0.80 | High (justify C; stop infinite research) |
| Bad data / process failure | 0.05–0.15 | Negative (wasted spend) |
| Refuse paid data → C now | 1.0 conditional | Medium-high certainty on free constraints; residual options uncertainty remains |

**Net:** Funding a **good** options history is positive EV for **truth**. Funding a **bad** series or running free filler is negative EV.

---

## 8. Major risks register (Phase 2)

| Risk | Mitigation |
|------|------------|
| GEX is folklore / non-causal | Falsifiers; modest P(success); hard stop |
| Vendor non-PIT | DR veto; fail closed |
| Completion bias | One programme cap; default cancel culture |
| Mandate too tight for real edges | Explicit Phase 3 only after C |
| Product claims overshoot science | Dual-track rules; no alpha marketing |
| Infinite Phase 2 | 60-day cap + null→C |

---

## 9. What human must decide (before any implementation)

1. **Fund Path B/B+** (approve paid options OI/gamma history under §6.4 + USD cap) **or**  
2. **Accept Path S** (formalise C; freeze alpha; optional productise) **or**  
3. **Open Phase 3 charter discussion** (mandate expansion) — **instead of or after** Phase 2, not smuggled in  

Until one of these is chosen, **no Phase 2 implementation**.

---

## 10. Implementation gate (future)

Implementation of Phase 2 may begin only when **all** hold:

- [ ] Human selects B, B+, or S (or explicit Phase 3)  
- [ ] If B/B+: vendor chosen, ToS OK, USD cap set, data pinned, PIT audit written  
- [ ] SR Attack Memo with soft veto lifted or no veto  
- [ ] DR admissibility signed  
- [ ] Programme design YAML pre-registered **before** first backtest  
- [ ] Phase 2 budget counters created (analogous to `phase1_budget.json`)  

**Not yet authorised.**

---

## 11. One-page recommendation

**Phase 2 should not be a second free-research season.**  
Phase 1 already answered: under free admissible daily data and long/flat constraints, confirmatory-grade edge was not found.

**Optimal Phase 2** is a **single, expensive-in-attention, cheap-in-count** test of the last high-EV structural channel (options positioning), with:

- scientific integrity preserved (frozen gates, falsifiers, family budget),  
- economic honesty (proxy risks accepted explicitly),  
- organisational honesty (hard stop → C on null),  
- optional product dual-track so the lab’s residual value is not held hostage to alpha.

If the human will not fund quality options history, the optimal move is **not** weak free programmes — it is **stop (C)** and, if desired, productise the rejection engine.

---

*Roles: RD, SR, LR, DR, IE, EA per `docs/INTERNAL_ORGANISATION.md`.*  
*Belief prior: `research_kb/rd/RD_BELIEF_STATE.md`.*  
*Phase 1b EIR (data detail): `docs/EVIDENCE_INVESTMENT_REVIEW_PHASE1B_OPTIONS_GAMMA_2026-07-30.md`.*
