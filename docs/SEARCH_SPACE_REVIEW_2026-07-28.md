# Research Programme Discovery — Search Space Review

**Date:** 2026-07-28  
**Directive:** Research Programme Discovery (new hypothesis *classes*, not indicators)  
**Stance:** Multiple independent info classes under frozen gates → **0 confirmatory survivors**. That is evidence the **search space may be incomplete**, not that the lab is broken.

**Objective of this document:** Decide whether we are exploring the **correct scientific search space**, and if not, propose how to change it (Roadmap V2).

Public literature is treated as **incomplete evidence**. No proprietary strategies to copy.

---

## 1. What search space we have actually explored (V1)

| Axis | V1 default | Evidence |
|------|------------|----------|
| **Prediction target** | Directional long-only full/flat BTC (and ETH plumbing) | Uniform across programmes |
| **Horizon** | Daily (selective 4h power) | Mostly 1d |
| **Features** | Causal OHLCV technicals; funding/OI; free on-chain clones; PM odds; FRED macro level/z | Broad nulls / conf kills |
| **Hypothesis form** | Sticky boolean entry/exit rules | Fixed rule language |
| **Validation** | Frozen gates, explor/conf, costs, WF | Intact — **not** the failure mode |
| **Success metric** | After-cost Sharpe + trade count + robustness | Unchanged |

**Pattern of results:** Val teases die on confirmatory; short alt series starve `min_trades`; level filters on public daily series do not clear the bar.

**Interpretation (hypothesis):** We have thoroughly stress-tested a **narrow generative grammar**:

> *daily public state variable → long or flat → survive frozen Sharpe/trade gates*

That grammar may be the wrong **scientific object**, not merely the wrong **variable**.

---

## 2. New research directions (hypothesis classes)

Scores: Sci EV / Complexity / Overfit risk (1–5; higher EV better; higher complexity/overfit worse).  
**Programme?** yes = deserves a new programme version when data exists.

### D1 — Conditional / regime-dependent relationships

| | |
|--|--|
| **Mechanism** | Edge exists only in some states (vol regime, liquidity, macro); average effect is zero |
| **vs V1** | V1 mostly tested **unconditional** long/flat on a feature. Conditioning is a *different hypothesis class* (interaction / state-dependent β) |
| **PIT** | Yes if state and signal both lagged |
| **Sci EV** | 4 | **Complexity** | 3 | **Overfit** | 4 (interaction multiplies trials) |
| **Programme?** | **Yes (V2 core)** — but with **pre-registered states only** (e.g. high/low realized vol from past data) and tight family budget |

### D2 — Market microstructure (own-market)

| | |
|--|--|
| **Mechanism** | Short-horizon imbalance, adverse selection, Roll/VPIN-style toxicity proxies predict next returns or vol |
| **vs V1** | V1 is daily bar filters; microstructure is **process of trading**, not end-of-day level |
| **PIT** | Hard without quality trades/L2; easy to leak |
| **Sci EV** | 3 (lit interest in crypto) | **Complexity** | 5 | **Overfit** | 5 |
| **Programme?** | **Defer** for personal spot daily mandate; wrong capital/horizon unless we **change target** to short-horizon research only |

### D3 — Cross-market information transfer

| | |
|--|--|
| **Mechanism** | Information in BTC microstructure/vol/returns leads ETH (or vice versa); funding/basis leads spot |
| **vs V1** | V1 is single-asset features; transfer is **leader–follower / multi-asset information flow** |
| **PIT** | Yes with lagged cross features (BTC closed before ETH decision) |
| **Sci EV** | 4 | **Complexity** | 3 | **Overfit** | 3 |
| **Programme?** | **Yes (V2)** — e.g. BTC→ETH or perp basis→spot with pre-reg lag; fits multi-asset plumbing |

### D4 — Volatility forecasting (not direction)

| | |
|--|--|
| **Mechanism** | Predict **risk** (σ, range, jump risk), not sign of return |
| **vs V1** | Entirely different **prediction target**; edge may be better risk timing / flat when forecast vol high |
| **PIT** | Yes with causal realized vol features |
| **Sci EV** | 4 | **Complexity** | 2–3 | **Overfit** | 3 |
| **Programme?** | **Yes (V2)** — primary metric becomes vol forecast skill **or** economic use of forecast (size/flat), still fail-closed |

### D5 — Uncertainty estimation / probabilistic prediction

| | |
|--|--|
| **Mechanism** | Predict distribution / confidence; trade only when forecast is calibrated and sharp |
| **vs V1** | V1 is hard long/flat; probabilistic is **different decision theory** |
| **PIT** | Yes |
| **Sci EV** | 3.5 | **Complexity** | 4 | **Overfit** | 4 |
| **Programme?** | **Yes later** — after vol-forecast class; keep rules simple (e.g. only trade when predicted |E[r]| > threshold from past) |

### D6 — Market state classification (latent regimes)

| | |
|--|--|
| **Mechanism** | Discrete states (trend/chop/stress) with different optimal policies |
| **vs V1** | Related to D1; V1 used simple vol labels lightly, not policy-per-state programmes |
| **PIT** | Expanding/causal labels only |
| **Sci EV** | 3.5 | **Complexity** | 3 | **Overfit** | 4 |
| **Programme?** | **Yes (merge with D1)** — pre-reg 2–3 states max |

### D7 — Adaptive model selection / model confidence sets

| | |
|--|--|
| **Mechanism** | Choose among models by recent OOS score; avoid permanent single rule |
| **vs V1** | V1 freezes one rule; adaptive selection is **meta-hypothesis** |
| **PIT** | Yes if selection uses only past folds |
| **Sci EV** | 3 | **Complexity** | 4 | **Overfit** | **5** (selection is a trial) |
| **Programme?** | **Defer** until several base models exist; needs multiplicity accounting |

### D8 — Risk management as edge

| | |
|--|--|
| **Mechanism** | Edge is superior **capital preservation** / drawdown control, not higher mean return |
| **vs V1** | V1 optimises Sharpe/long-only; risk-as-edge changes **objective** |
| **PIT** | Yes |
| **Sci EV** | 4 for personal mandate | **Complexity** | 2 | **Overfit** | 3 |
| **Programme?** | **Yes (V2)** — e.g. pre-reg vol-target or max-DD stop policies evaluated on **utility / Calmar / DD constraints** with frozen secondary gates |

### D9 — Behavioural / structural mechanisms (beyond level filters)

| | |
|--|--|
| **Mechanism** | Weekend effects already weak; funding crowding spent; **ETF flow**, **options expiry**, **miner behaviour** as structural |
| **vs V1** | Partial overlap with spent alt-data; **ETF flow** still relatively fresh |
| **PIT** | ETF: yes with lag; options: harder |
| **Sci EV** | 3–3.5 (ETF) | **Complexity** | 2–3 | **Overfit** | 3 |
| **Programme?** | **Yes selective** — ETF flow only if free reconstructible series; not more CMD clones |

### D10 — Entirely different prediction targets

| Target examples | Why different | Programme? |
|-----------------|---------------|------------|
| Next-day **range / vol** | D4 | Yes |
| **Probability of large drawdown** in N days | Risk class D8 | Yes |
| **Relative** BTC vs ETH return sign | Cross-asset D3 | Yes |
| Trade **execution cost** prediction | Ops, not alpha | Defer |
| Directional with **shorts** | Mandate change | Only with explicit policy revision |

### D11 — Microstructure (literature-heavy, crypto active)

Public work (e.g. Roll/VPIN and cross-asset effects in crypto) suggests **some** predictability in short-horizon dynamics once leakage/costs controlled — but effect sizes and AUC often modest, and **not aligned** with tiny spot daily personal trading without data/ops overhaul.

**Programme?** Research-only **defer** unless mandate expands to short-horizon research without live expectation.

---

## 3. Synthesis: is the V1 search space wrong?

| Hypothesis | Assessment |
|------------|------------|
| Gates too strict | **Not supported** as first fix — science integrity is the product |
| Wrong variables only | **Insufficient** — many variable classes already null |
| Wrong **hypothesis grammar** (unconditional daily long/flat on public levels) | **Supported** by pattern of results |
| Wrong **prediction target** (direction only) | **Supported** — vol/risk targets underexplored with our data |
| Wrong **asset coupling** (single-name) | **Plausible** — cross-asset transfer untested |
| Need paid data first | **Not first** — search-space change can start with free OHLCV multi-asset + vol targets |

**Conclusion:** The laboratory should **not** keep sampling V1 grammar. It should adopt a **Version 2 research search space** that prioritises **new hypothesis classes** (conditioning, cross-asset transfer, vol/risk targets, risk-as-edge) under **unchanged validation standards**.

---

## 4. Overfitting and economy rules for V2

1. **One programme = one class** (not five indicators of the same class).  
2. Pre-register **states and lags** before seeing outcomes.  
3. Family trial ledger mandatory; hard cap on exploratory hyps per class (≤5).  
4. Prefer **different targets** over new free on-chain levels.  
5. Reject “adaptive ML soup” until simple class programmes exist.  
6. Paid data only after free V2 classes + EIR.

---

## 5. What we are *not* doing

- Copying published “winning” crypto ML accuracies (often weak OOS / different metrics)  
- Softening min_trades/Sharpe to fit short samples  
- Reopening SMA/volume clone factories  
- Building L2 stack for personal AUD-scale live  

---

## 6. Deliverable

**Version 2 Research Roadmap:** `docs/RESEARCH_ROADMAP_V2.md`
