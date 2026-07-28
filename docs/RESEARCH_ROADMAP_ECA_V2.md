# Research Roadmap — Evidence Channel Architecture (ECA)

**Version:** ECA-V2 (supersedes standalone “V2 programme list” as *default framing*)  
**Date:** 2026-07-28  
**Basis:** `docs/ARCHITECTURE_EVIDENCE_AGGREGATION_STUDY.md`  
**Standards:** Frozen economic gates, PIT, explor/conf, no leverage — **unchanged**

---

## Thesis

V1 exhausted **atomistic signal→trade** search.  
V2 correctly introduced **new hypothesis classes**, but still risks atomism at class level.  

**ECA:** Discover and validate **calibrated evidence channels**, then a **single frozen aggregator + decision policy**, tested as one system under existing gates.

---

## Architecture layers

| Layer | Object | Success metric (examples) |
|-------|--------|---------------------------|
| **Channel** | Numeric evidence `e_i` (PIT, versioned) | Calibration + skill on *claimed* target (vol, trend support, macro stress, …) |
| **Aggregator** | `a = A(e_1,…,e_k)` | Val only; prefer equal weight / pre-reg map |
| **Decision policy π** | Long / flat / size from `a` + risk envelope | **Full frozen gates** (Sharpe, trades, WF, costs, …) |
| **Ops** | Paper → shadow → live | Unchanged ladder |

LLM “agents” optional for offline ideation only; **promotion path is numeric only**.

---

## Phased plan

### Phase ECA-0 — Protocol (docs + thin schema, short)

- Evidence record schema (score, asof, inputs_hash, version).  
- Rules: channel pre-reg; aggregator pre-reg; no test tuning; family ledger counts channel versions.  
- Explicit ban: free-text committee votes as promotion evidence.

### Phase ECA-1 — Channel #1: Vol / Risk (modified V2-A)

**Not:** “find a long rule that uses vol.”  
**Yes:**  

1. Forecast next-horizon realized vol / range (skill + calibration).  
2. Emit evidence `e_risk` ∈ [0,1] = “risk-off pressure” (high = prefer flat).  
3. Optional provisional policy π₁ for diagnostics only; **promotion requires ECA-3+**.

Data: BTC OHLCV already in lab.  
Complexity: low–medium. Overfit: controlled with ≤4 locked variants.

### Phase ECA-2 — Channel #2: Structure or Cross-asset

Pick **one**:

- **ECA-2a** Lagged trend/structure score `e_trend`, or  
- **ECA-2b** BTC→ETH transfer score `e_xasset`  

Same discipline: evidence first, not trade first.

### Phase ECA-3 — Aggregator v0 + Decision policy

- Inputs: `e_risk`, `e_trend` (or xasset).  
- **A₀ = equal weight** (default) or one pre-reg logistic fit on **train only**.  
- π₀: e.g. long only if A₀ > τ and e_risk < ρ (τ,ρ pre-reg).  
- Exploratory on val; confirmatory on test **once**.

### Phase ECA-4 — Optional channels

Macro (FRED — already null as *atomistic* filters; may still add as **calibrated** `e_macro` if redesigned), ETF flow, vendor inventory — only if they improve ablation OOS.

### Explicitly out of order

- Multi-agent LLM debate product  
- Paid data before ECA-1/2 free channels  
- Softening gates so the committee “always has a trade”

---

## Mapping from prior V2 list

| Old V2 | ECA placement |
|--------|----------------|
| V2-A Vol forecast | **ECA-1** (channel) |
| V2-B Cross-asset | **ECA-2b** |
| V2-C Conditional trend | **ECA-2a** / state in channel |
| V2-D Risk-as-edge | Part of **π** (decision), not a separate “alpha signal” |
| V1 level filters | Retired as default channel design |

---

## Success metrics

| Success | Failure mode |
|---------|----------------|
| Calibrated channels with independent ablation value | Pretty dashboards |
| Aggregator survives confirmatory under frozen gates | Weight fishing on test |
| Honest “flat” when evidence weak | Forced always-long committee |
| Uncertainty reduced on architecture | Repo complexity for its own sake |

---

## Immediate next step (after human/process accept of this study)

1. Implement **ECA-0** schema (minimal).  
2. Implement **ECA-1** vol/risk channel (modified V2-A).  
3. Do **not** promote ECA-1 alone to APPROVED trading without aggregator path unless it independently clears full gates (optional side path).

---

## One-line roadmap

**Build a committee of calibrated evidence, not a zoo of lonely indicators — starting with risk/vol evidence, then a second independent channel, then one frozen aggregator under the same gates that already reject noise.**
