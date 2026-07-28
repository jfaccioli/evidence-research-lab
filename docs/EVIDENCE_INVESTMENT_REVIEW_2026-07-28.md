# Evidence Investment Review — 2026-07-28

**Authority:** Explicit request before any paid dataset  
**Objective:** Maximise **expected scientific value per dollar and per human hour**  
**Standards:** Frozen gates; no leverage; paid ≠ better by default  
**Related:** Alpha Discovery, Evidence Acquisition Roadmap, Human Action Packet (superseded on spend)

---

## 1. Decision framework

For each candidate information class, score (1–5; higher better unless noted):

| Dimension | Meaning |
|-----------|---------|
| **Pred** | Expected predictive / scientific content for *our* mandate |
| **PIT** | Point-in-time integrity if used carefully |
| **Hist** | Historical depth vs train/val/test + min_trades |
| **Unique** | Not a re-expression of a spent lab operationalisation |
| **Impl** | Inverse effort (5 = drop-in) |
| **$/hr** | Inverse cost burden (5 = free + minutes) |
| **Edge** | Expected contribution to *robust* edges under frozen gates |
| **Risk** | Inverse of major scientific/legal risk (5 = low risk) |

**Invest money only if:** EV of paid path **clearly exceeds** EV of **all remaining free alternatives**, including free-but-human unlocks (e.g. free API registration).

---

## 2. Baseline: what we already know (cost = 0)

| Information already tested | Outcome under frozen gates |
|----------------------------|----------------------------|
| BTC daily technicals | Exhausted nulls |
| Public funding / OI | Null / conf kill |
| Free CMD netflow / stablecoin / premium / liq / MVRV | Null / conf kill |
| PM single binary + **PM multi-leg panel** | Expl 0/5 each |
| Lab pipeline | Ready; not the bottleneck |

**Implication:** Paying for *another daily free-style on-chain metric* or *another single PM binary* has **near-zero incremental EV**.

---

## 3. Candidate external classes (comparison)

Scores are **judgemental**, not market prices of alpha. Treat as hypotheses.

### A. Free FRED (or equivalent) macro daily series — *registration only, $0*

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 3.5 | 5 | 5 | 4 | 4 | **5** | 3.5 | 4 |

- **Mechanism:** USD / rates / liquidity regime as **state** for BTC risk appetite.  
- **Cost:** $0; ~10–20 min human for free API key.  
- **Legal:** Public US government data (standard terms).  
- **vs lab:** **Unexplored** information class (not another CMD clone).  
- **Risks:** Weak link to BTC; macro is crowded; still may null under gates.  
- **Verdict:** **Highest value-per-dollar of any external unlock.**

### B. Free multi-source prediction-market **archives** (expanded panel / Kalshi / multi-event)

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 3 | 3 | 3–4 | 2–3 | 3 | 5 | 2.5 | 3 |

- **Already partially tested:** path panel on 2025 BTC markets → expl null.  
- **Residual free value:** non-path events (policy, macro PM), longer Kalshi history, event residuals.  
- **Risks:** Collinearity with BTC path; short liquid history; more assembly hours.  
- **Verdict:** **Defer further large free PM assembly** until macro tried; marginal after path-panel null.

### C. Vendor exchange netflow / reserves (CryptoQuant / Glassnode-class) — **PAID**

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 3.5 | **4.5** | 5 | 2.5 | 4 | 2 | 3 | 3 |

- **Mechanism:** Labeled inventory / exchange supply (same *family* as free netflow).  
- **Why not automatic “better”:** Free netflow already **conf-null**; paid mainly buys **label quality + revision process**, not a new mechanism class.  
- **Cost:** ~USD 30–100+/mo public tiers, or export; annual can exceed personal research ROI if subscription open-ended.  
- **Legal:** Vendor ToS; no redistribution; research use only.  
- **Risks:** Expensive null; same sticky long-only failure mode; revision look-ahead if misused.  
- **Verdict:** **Do not buy yet** — free macro (A) still untested and dominates value-per-dollar.

### D. Spot Bitcoin ETF flow history — free tracker vs paid API

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 4 | 3–4 | 2–3 | **4.5** | 3 | 3–4 | 3.5 | 3 |

- **Mechanism:** Institutional creation/redemption demand pipe (post-2024).  
- **Literature:** Preliminary claims of short-horizon association with BTC (causal claims unproven; must pass our gates).  
- **Cost:** Some trackers free scrape (fragile); CoinGlass-class API needs key (paid tiers common).  
- **Hist:** Short sample since spot ETF launch → hard for min_trades + splits.  
- **Verdict:** **Interesting uniqueness**, but **history short**; free path first if any stable public CSV; **do not pay** until free macro done and sample-design plan exists.

### E. Social / X historical archive

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 3 | 2 | 2 | 4 | 1 | 1 | 2 | 2 |

- **Verdict:** **Defer** — high cost/effort, weak free PIT, not first dollar.

### F. Options skew / vol surface

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 3 | 3 | 3 | 4 | 2 | 1 | 2 | 2 |

- **Verdict:** **Defer** — cost and complexity vs personal long-only daily mandate.

### G. L2 order book / HFT feeds

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 2 | 2 | 3 | 3 | 1 | 1 | 1 | 2 |

- **Verdict:** **Reject** for this mandate.

### H. More free CMD daily metrics

| Pred | PIT | Hist | Unique | Impl | $/hr | Edge | Risk |
|------|-----|------|--------|------|------|------|------|
| 1 | 2 | 4 | 1 | 5 | 5 | 0.5 | 4 |

- **Verdict:** **Reject** — spent.

---

## 4. Ranked investment report

| Rank | Investment | Cash cost | Human hours | Composite (science per $ and hr) | Recommendation |
|------|------------|-----------|-------------|----------------------------------|----------------|
| **1** | **Free FRED (or equivalent) API key + macro regime programme** | **$0** | ~0.3–1 h | **Highest** | **Do this first** |
| **2** | Free ETF flow CSV if stable public source found | $0 | 1–4 h | High uniqueness, short hist | Autonomous hunt / optional human pointer |
| **3** | Expanded free PM non-path events (after macro) | $0 | 4–12 h | Medium after path-panel null | Defer |
| **4** | Vendor netflow **one-time export** | ~$30–200 one-shot* | 1–2 h + export | Medium (quality↑, mechanism family spent) | **Only after #1 null or blocked** |
| **5** | Vendor open subscription | $300–1200+/yr | low | Poor $/science if open-ended | **Reject default** |
| **6** | Social / options / L2 | High | High | Poor | Defer / reject |

\*Order-of-magnitude; not a quote.

---

## 5. Final recommendation

### Single highest-priority investment

**Not a paid dataset.**  

**Priority #1:** Obtain a **free** FRED (or equivalent public macro) API key and enable daily series such as broad USD index / policy rate proxies for a **pre-registered macro-regime programme**.

### Why it ranks first

1. **$0 cash** — maximises science per dollar by definition among positive-EV options.  
2. **Unexplored information class** — not a re-test of free on-chain clones or PM path odds.  
3. **Excellent PIT and multi-decade history** — fits train/val/test and min_trades.  
4. **Drop-in tooling exists** (`external` series attach).  
5. Paid vendor netflow is **same mechanism family** as free netflow that already failed confirmatory.

### Why lower-ranked alternatives were rejected or deferred

| Alternative | Why not first |
|-------------|----------------|
| **Pay for CryptoQuant/Glassnode now** | Free macro still untested; paid mostly upgrades a **spent family** (inventory flow); fails “clearly exceeds all free alternatives” |
| Open-ended data subscription | Poor science-per-dollar; prefer fixed export later if needed |
| More free PM path panels | Already null; diminishing returns |
| More free CMD metrics | Rejected (spent) |
| Social / options / L2 | Cost, PIT, or mandate mismatch |
| ETF paid API | Short history; free source first; after macro |

### Exact minimum data required (for #1)

| Field | Spec |
|-------|------|
| Series | Daily USD strength and/or short-term rate proxy (e.g. FRED: trade-weighted USD and/or federal funds / 2Y equivalent) |
| Columns after ingest | `event_time` (UTC day-end + lag policy), `value` |
| Lag policy | Publish lag ≥1 calendar day (pre-reg in programme) |
| Length | Full available history (multi-year preferred) |
| Cost | **$0** + free key registration |

### First pre-registered programme that would use it

**`PROGRAMME_MACRO_REGIME_V1`** (to lock before results):

- Mechanism: risk-off when USD strengthens / rates jump; long only when regime not hostile + mild trend.  
- ≤5 hyps; prefix `mac_`; frozen gates; temp registry.  
- Explicitly **not** a technical clone: features from macro series only + existing trend flags.

### Expected scientific gain if it **succeeds**

- First exploratory (and possibly confirmatory) signal from a **new information class**.  
- Unlocks paper-clock path **if** confirmatory earned (still no automatic live).  
- Validates macro-as-state research line under our standards.

### Expected scientific gain if it **fails** (null)

- **High-quality null:** macro daily regime filters do not clear frozen long-only BTC gates in this operationalisation.  
- Justifies escalating to **next** investment tier (ETF free/paid design, or **then** vendor netflow export).  
- Prevents spending money while a free orthogonal class was untested.

---

## 6. Paid spend decision (this review)

| Question | Answer |
|----------|--------|
| Is commercial data assumed superior because paid? | **No** |
| Does paid vendor netflow **clearly** beat remaining free options on science-per-dollar? | **No** |
| **Spend money now?** | **No** |
| Interrupt human for paid acquisition? | **No** |
| Interrupt for free FRED key? | **Optional / low friction** — recommended when you have 15 minutes; not a paid investment |

---

## 7. Standing actions after this review

1. **Do not purchase** CryptoQuant/Glassnode/social/options feeds on the basis of prior HAP alone — this EIR **supersedes** “buy vendor first.”  
2. Update Human Action Packet: primary human unlock = **free FRED key** (or drop free macro CSV); paid export is **tier-2**.  
3. When free macro is available: lock programme → ingest → `run-programme` → autopsy.  
4. Re-run EIR before any cash outlay.

---

## 8. One-sentence conclusion

**Maximise science per dollar by testing free macro regime information before any paid on-chain vendor; commercial netflow is not justified while that free alternative remains untried.**
