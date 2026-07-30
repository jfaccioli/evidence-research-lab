# Research Director — Belief State

**Updated:** 2026-07-30 (post Phase-1 free path; EV-max operating mode)  
**Mode:** Maximise P(correct conclusion about deployable edge) per remaining resource  
**Not optimising:** programme count, code volume, apparent productivity  

## Operating principle (binding)

A cancelled programme after careful multi-role criticism is a **success**.  
A weak programme that burns a major-programme slot or confirmatory eval is a **management failure**.

---

## 1. Hard constraints (current)

| Resource | State |
|----------|--------|
| Phase 1 conclusion | **`B_richer_data_justified`** (issued) |
| Major inefficiency slots | **0 / 3 remaining** |
| External dataset pins | **0 / 2 remaining** |
| Confirmatory-class evals | **8 / 10 remaining** (unspent on free inefficiency progs) |
| Paid spend default | **$0** until human approval |
| Shadow-eligible candidates | **0** |
| Architecture | **Frozen** |

**Implication:** Free-path *major* science under Phase 1 is **closed**. Further free long/flat fishing that reopens retired families or invents near-clone free proxies would violate both budget discipline and EV optimisation.

Human must fund Phase 1b (paid data) **or** accept **C** / pause / productise.

---

## 2. What we believe we know (Bayesian summary)

Posterior language: *credence that a confirmatory-grade long/flat edge exists under our envelope* for each mechanism class.

| Mechanism class | Prior (start Phase 1 ineff) | Posterior now | Why updated |
|-----------------|----------------------------|---------------|-------------|
| Free OHLCV technicals (mom, breakout, vol filters, calendar, …) | Low | **Very low** | Massive exploratory mass; PCS vol-scale & basis risk-off C_rejected; thesis tree failures dominate |
| Exchange netflow / inventory free CMD | Medium-low | **Very low** | Confirmatory 0/6 on flow family; stablecoin exchange netflow exploratory null |
| ETF primary-market aggregate flows (lag-1 free Farside) | Medium | **Low** | Programme 0/4; return→flow > flow→return; industry/practitioners emphasise flows *confirm* not predict daily |
| System stablecoin Δlog supply as mint/burn proxy | Medium-low | **Low** | Property char already near-null direction; formal gates 0/4; overlaps risk-on beta |
| Miner revenue Δlog stress proxy | Low-medium | **Low** | 0/4; high Sharpe tease with n_trades&lt;30 correctly killed; inventory missing |
| Options dealer gamma / hedging | Medium-high | **Medium-high (untested)** | Not falsified by us; equity GEX literature + large Deribit OI; **blocked on historical PIT data** |
| Institutional TWAP / microstructure | Medium | **Medium (untested)** | Needs intradaily; out of free daily budget |
| True vendor PIT reserves | Low-medium | **Low-medium** | High overlap risk with conf-null free netflow operationalisation |

**Global posterior on free-shelf daily long/flat BTC edge under our gates:** **low**.  
**Global posterior that *some* richer information class could still contain edge:** **non-trivial** — concentrated in **options market structure**, not another free transform.

---

## 3. Contradiction search (what doesn’t fit)

1. **ETF literature vs our null**  
   - Academic work reports cointegration / Granger association between ETF *assets/flows* and BTC price (level equilibrium, long-run demand).  
   - Practitioner sources stress that **daily net flows do not reliably forecast next-day returns** and often lag price.  
   - **Resolution:** Level/cointegration ≠ deployable lag-1 long/flat signal after costs. Our null does **not** contradict long-run demand pressure; it falsifies *our* operationalisation for promotion.

2. **Miner stress Sharpe tease**  
   - `hyp_mrv_stress_flat` val Sharpe ≈ 1.45 with 24 trades.  
   - **Resolution:** Gate min_trades and sample fragility; do **not** promote or expand family to “get 30 trades.” That would be p-hacking. Learning: sparse stress flags are statistically fragile under daily bars.

3. **PCS / funding / basis vs crypto-carry literature**  
   - BIS/crypto-carry work: structural limits to arbitrage, volatile convenience yields.  
   - Edges often **delta-neutral / funding capture**, not spot long/flat.  
   - **Resolution:** Our mandate forbids the natural form of those edges (leverage/short/hedged). Long/flat translations (basis risk-off, funding filters) already failed PCS/gates.

4. **Stablecoin transmission ranking vs characterization**  
   - Catalogue ranked it highly with partial data; property doc already said don’t fish long/flat on supply growth.  
   - **Resolution (management critique):** Opening a full major programme after characterization near-null was **low EV use of a scarce slot**. Prefer cancellation after review next time.

---

## 4. Internal multi-role debate (required disagreement)

### Research Director
- Free major budget is spent; do not invent “programme 4.”  
- Correct scientific action now is **belief quality + paid-data EIR**, not more free nulls.  
- Highest untested EV: **dealer gamma / options OI structure** with historical PIT.

### Scientific Reviewer (attack)
- **Critique of prior cycle:** Stablecoin and miner programmes should have been **cancelled** under stricter EV bar; they burned two of three major slots after ETF already null’d the best free structural idea.  
- Miner without inventory is mechanism theatre.  
- Stablecoin Δlog was pre-emptively weakened by characterization.  
- Conclusion **B** is only justified if options paid data truly has higher EV than stopping; otherwise prefer **C** to avoid infinite “one more vendor.”

### Literature Reviewer
- Equity options: dealer gamma / GEX associated with mechanical hedging flows near large OI nodes (industry research denser than academic crypto).  
- Crypto: Deribit dominates BTC options OI (tens of $B notional at peaks); expiry and strike concentration are public narratives.  
- ETF: cointegration papers support *structural demand*, not daily signal.  
- Funding/basis: predictive content exists for **derivatives pricing/arb**, weak translation to spot long/flat under our costs.

### Data Reviewer
- Deribit **live** book summary: OI available now; **greeks not** in free book summary.  
- Free historical options *OHLCV* (e.g. aggregate CDD-style) **without OI** cannot reconstruct dealer gamma honestly.  
- Building a “fake gamma” from price-only options marks = look-alike to IV/vol families already stressed.  
- **Fail closed** on free historical gamma. Paid snapshot history (Amberdata / GVol / similar) or one-time export required.  
- ETF free path was admissible; we used it correctly once.

### Implementation Engineer
- Lab can attach external/flow series and run frozen gates without new architecture.  
- No new subsystems until a funded series is pinned with PIT policy.

### Experiment Auditor
- Gates correctly killed sparse high-Sharpe miner hyp.  
- Do not re-open families with “almost 30 trades.”  
- Confirmatory budget of 8 must not be spent on exploratory fishing disguised as new families.  
- PCS already consumed 2 confirmatory-class evals.

**Disagreement product:**  
- Reviewer prefers **C** unless paid options EIR is specific, capped, and one-shot.  
- Director holds **B** with **strict** one-dataset Phase 1b proposal (below).  
- Both reject more free major programmes.

---

## 5. How ranking should change (learning extraction)

| Event | Wrong assumption | Ranking change |
|-------|------------------|----------------|
| ETF free null | “Structural channel ⇒ daily long/flat edge after lag+costs” | ↓ free structural *daily* signals; keep structural *demand* as background fact |
| Stablecoin programme | “Catalogue rank + partial data ⇒ must open programme” | ↑ bar: characterization near-null + distinctness required; cancel before open |
| Miner programme | “Free proxy is better than leaving slot idle” | Idle slot with high option value for paid data &gt; burning slot on weak proxy |
| Mass OHLCV nulls | “More hyps find edge” | ↓ all free technical near-clones permanently under Phase 1 |
| Flow conf-null | “Whale/exchange flow is the edge” | ↓ free CMD-style netflow; only vendor non-revised PIT could reopen |

**Belief about Research Director process:**  
Prior autonomous cycle **over-weighted completion**. New prior: **expected information value / slot** must clear a high bar; default action is **cancel**.

---

## 6. Phase 1b proposal (only if human funds)

### Single allowed acquisition target

**Name:** Historical BTC options **open interest by strike/expiry** + mark IV (and greeks if included) on Deribit (or vendor-normalised equivalent), daily or better, with snapshot timestamps suitable for PIT.

**Not allowed in this EIR:** open-ended multi-asset terminal; alternative data package bundles; second free ETF re-scrape variants; another netflow vendor “because free failed.”

### Why this dataset (not another)

1. **Mechanism untested** by the lab; not a clone of retired free families.  
2. **Economic story:** dealer hedging near high-gamma nodes can force pro-cyclical spot/perp flow; lag comes from risk limits and discrete hedge rebalancing.  
3. **Literature/industry prior:** GEX-style effects; crypto options OI is large and concentrated on Deribit.  
4. **Free path exhausted:** live OI ≠ historical PIT; free options OHLCV without OI is insufficient.  
5. **Maps to mandate:** can define long/flat or size-down rules around expiry/gamma regimes without leverage *as hypothesis* (execution still long/flat only).

### Minimum programme if data lands

- Pre-register ≤4 hyps; ≤1 confirmatory.  
- Features must be causal functions of **lagged** OI/gamma snapshots only.  
- Explicit falsification: expiry calendar dummy alone; pure RV; pure mom.  
- If null → move Phase 1 from **B** to **C** (do not chain more paid datasets without new human EIR).

### Cost doctrine

- Prefer **one-time history export** over subscription.  
- Cap: human-set USD; RD default recommends smallest history that covers ≥2 years of weekly expiries if price allows.  
- **No auto-purchase.**

---

## 7. What we will not do

- Open new free major inefficiency programmes under Phase 1 (budget 0).  
- Reopen ETF / free netflow / mom / vol-scale / basis-riskoff / stablecoin-exchange-flow / miner-revenue families.  
- Soften min_trades or gates to “save” a tease.  
- Spend confirmatory budget without exploratory survivor.  
- Build architecture instead of deciding B vs C.  
- Copy published strategies; only extract mechanisms.

---

## 8. Interrupt status

| Condition | Status |
|-----------|--------|
| Shadow-eligible candidate | No |
| Paid dataset with strong justification | **Yes — awaiting human** (this document §6) |
| Fundamental flaw in prior conclusions | No (self-critique of *process*, not of gate results) |
| Safety | No |
| Phase 1 free path complete | **Yes — B issued** |

**Human choice set:** fund Phase 1b options history **or** accept **C** / pause / productise research OS.

---

## 9. Success metric reminder

Success = **uncertainty reduction** about where edges can live.  
Free-path nulls under honest gates are **knowledge**.  
The remaining uncertainty is almost entirely: *does options market structure contain a deployable signal we have not yet measured?*

*End of belief state.*
