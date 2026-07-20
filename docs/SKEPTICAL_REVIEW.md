# Skeptical Quant Review — Architecture Weaknesses & Revisions

**Role:** Quantitative researcher hired to find holes before any code is written.  
**Inputs:** Original Phase 1 plan + external review (Monte Carlo, regimes, Bayesian confidence, feature importance, data trust scores, literature agent, meta-analysis, SQLite).  
**Goal:** Strengthen the foundation; demote shiny features that inflate complexity without power.

---

## 1. Verdict

The original plan is methodologically sound for a personal research lab. The external review’s additions are **mostly correct as a long-term roadmap**, but several are **dangerous if naively added to Phase 1**.

**Revised stance:**

| Suggestion | Adopt? | When | Risk if rushed |
|------------|--------|------|----------------|
| SQLite registry | **Yes, immediately** | Phase 1 | JSON was the weakest scalability call |
| Monte Carlo / path resampling | **Yes, thin slice** | Phase 1 for candidates | Over-interpreting dependent returns |
| Regime labeling + stratified reports | **Yes, simple rules** | Phase 1 | ML regime models overfit |
| Bayesian-ish confidence | **Yes, pragmatic** | Phase 1 (posterior on mean trade / bootstrap) | Fake precision from bad priors |
| Feature importance | **Interface only** | Phase 2+ | Meaningless for single-rule hyps; SHAP theater |
| Data quality / trust scores | **Yes, minimal** | Phase 1 schema | Numeric scores become cargo-cult without audits |
| Auto literature review agent | **Stub + manual path** | Phase 2 | Unbounded API cost, non-reproducible “papers said so” |
| Meta-analysis of research | **Schema hooks** | Phase 2 (needs N≫1) | Empty dashboards with 5 hypotheses |

**Overall revised score after self-critique:** architecture still strong; main risk is **premature sophistication** and a few **subtle statistical lies**.

---

## 2. Hard weaknesses in the original plan

### 2.1 Multiple-testing theater

**Flaw:** Logging hypotheses and “mentioning” Deflated Sharpe is not the same as controlling false discovery.

With even 50 mildly related technical rules on the same BTC series, the chance of a lucky OOS fold is material. Bootstrap CIs on a **selected** strategy are optimistically biased if selection used the same data family.

**Fix:**
- Hard **research budget**: e.g. max K new hypothesis *versions* per calendar month that may touch the final test set.
- Test set is **one-shot per version**; retunes create `version+1` and consume budget.
- Report `family_id` + `n_in_family_tested` and apply a simple penalty (Bonferroni on alpha, or Deflated Sharpe with N = family size).
- Separate **exploratory** runs (val only, cannot promote) from **confirmatory** runs (may use test).

### 2.2 Walk-forward can still leak via human (or LLM) iteration

**Flaw:** WF prevents a single static overfit; it does not prevent the researcher from “trying another idea that looks like the one that almost worked” after seeing test.

**Fix:**
- Registry fields: `saw_test: bool`, `pre_registered_at`, `test_unlocked_at`.
- Policy: after test is run, **no parameter edits** on that id; only new ids.
- Phase 1 CLI: `run --confirmatory` requires frozen YAML hash matching registry.

### 2.3 Next-open fill is necessary but not sufficient

**Flaw:** On 4h/daily BTC, open-to-open is OK for research, but:
- Gaps / weekend structure (crypto is 24/7, so weaker issue).
- Funding not applicable (spot OK).
- **Open price may not be tradable at size** even for tiny AUD — less critical at 10–50 AUD.
- More serious: **signal uses close, fill uses next open** — good — but features like “vol below median” need a **causal median** (expanding or rolling past-only), not full-sample median.

**Fix:** Document and test: all thresholds that are distributional must be **rolling or expanding from past data only**. Full-sample quantiles are leakage.

### 2.4 Long-only BTC strategies mostly harvest beta

**Flaw:** Beating cash is trivial in a bull sample. Beating buy-and-hold on Sharpe while long-only is hard; many “edges” are **just less beta in drawdowns**.

**Fix:**
- Primary metrics must include **excess vs buy-and-hold** (active return, information ratio vs B&H, and/or capture ratios).
- Report **beta to BTC** and **BTC-adjusted returns** (simple: subtract B&H return path or residualize).
- A strategy that is “cash in bears, long in bulls” must be judged on whether timing is real or luck — MC + regime slices.

### 2.5 min_trades = 30 is still weak

**Flaw:** 30 trades on overlapping daily signals with strong autocorrelation ≠ 30 independent bets. Effective sample size can be ~5–15.

**Fix:**
- Report **average holding period**, **autocorrelation of returns**, rough **effective N**.
- Prefer metrics on **non-overlapping trade returns** with block bootstrap (not i.i.d. bootstrap).
- Monte Carlo should shuffle **trade returns in blocks** or resample paths with **stationary bootstrap**, not assume independence.

### 2.6 Cost model is a single fantasy number

**Flaw:** Fixed 10 bps + slip is fine as conservative default, but cost **depends on vol and liquidity regime**. Stressing 2× is good; still one-dimensional.

**Fix (Phase 1 light):** keep constant bps + 2× stress; add optional **vol-scaled slippage** (slip ∝ ATR%) as sensitivity, not as primary.

### 2.7 “Hypothesis generator” without constraints becomes idea spam

**Flaw:** LLM ideation will correlate highly (all momentum variants). Registry fills with pseudo-independent tests → multiple-testing explosion.

**Fix:**
- Generator emits into **taxonomy**: `trend`, `vol_filter`, `mean_reversion`, `calendar`, `volume`, `composite`.
- Cap tests per taxonomy per period.
- Literature agent (later) must map papers → taxonomy + **replication recipe**, not free-form hype.

### 2.8 Promotion gates can be gamed by metric shopping

**Flaw:** If gates say Sharpe OR DD improvement OR Calmar, researchers pick the one that passes.

**Fix:**
- **Single primary objective** pre-registered per hypothesis (default: after-cost Sharpe excess vs B&H, or Calmar excess — choose one lab-wide default).
- Secondary metrics are diagnostic only; cannot flip reject → pass alone.
- Lab default proposed: **after-cost Sharpe**, with **mandatory** B&H comparison panel (informational), plus hard DD and min-trade constraints as *constraints* not alternate objectives.

### 2.9 Reproducibility gaps still present

**Flaw:** Hashing data and git SHA misses:
- Non-deterministic float reduction order (minor).
- Dependency versions (`uv.lock` / pin essential).
- Timezone / exchange maintenance gaps in klines.
- Silent cache corruption.

**Fix:** lockfile in Phase 1; assert bar integrity; store engine `schema_version`; golden-file test on a tiny fixture series.

### 2.10 Research on tiny capital can distort design goals

**Flaw:** Optimizing for 10–50 AUD is correct for **future execution friction**, but research should still use **fractional equity** math, not “can I buy 0.0001 BTC” path dependence early. Dust and min notional matter later.

**Fix:** Phase 1 continuous fraction [0,1]; Phase 5 applies exchange min notional constraints.

---

## 3. External review items — deep dive

### 3.1 Monte Carlo — adopt with discipline

**What to implement in Phase 1 (candidates only):**

1. **Trade-return bootstrap (block):** resample blocks of trade PnLs → distribution of total return, max DD, Sharpe.  
2. **Path permutation under null (optional light):** scramble sign of active returns under null of no edge → p-value style statement.  
3. **Parameter sensitivity:** ±20% on key params (e.g. SMA window 160/200/240) on **validation only**; report fragility index = % neighbors that still pass gates.

**What NOT to do in Phase 1:**
- Fancy geometric Brownian path sims disconnected from actual trade list.
- Monte Carlo on the entire bar series without preserving vol clustering (misleading).

**Sequence risk question to answer in reports:**  
> “In what fraction of resampled trade sequences does max DD exceed X or terminal wealth underperform B&H?”

### 3.2 Regime detection — simple, causal, mandatory in reports

**Phase 1 regimes (rule-based, past-only):**

| Regime | Definition (example, config) |
|--------|------------------------------|
| Trend | `close > SMA(200)` vs `<` → bullish / bearish bias |
| Vol | 20d realized vol vs expanding median → high / low vol |
| Combined | 2×2: bull-low, bull-high, bear-low, bear-high |

Optional third axis later: sideways = |SMA slope| small.

**Report table:** metrics **per regime** (only bars/trades assigned by causal labels).  
**Gate (soft Phase 1):** do not auto-reject for single-regime concentration; **hard-warn** if >80% of excess return from one regime cell.

**Reject ML HMMs in Phase 1** — too easy to leak and overfit.

### 3.3 Bayesian confidence — pragmatic, not theological

Full hierarchical Bayes is overkill for Phase 1.

**Phase 1 “confidence” package:**
- Block-bootstrap distribution of Sharpe / mean trade return.  
- Optional: normal–normal conjugate posterior on **mean trade return** with weakly informative prior centered at 0 (shrinkage toward no edge).  
- Report: `P(mean_trade_return > 0 | data)` under that model, clearly labeled **model-dependent**.

This answers “how confident?” better than a point Sharpe, without pretending we have a full market generative model.

### 3.4 Feature importance — defer logic, keep interface

For Phase 1 single-rule hypotheses, “22% sentiment / 18% funding” is **fiction**.

**Phase 1:** `FeatureSpec` list on hypothesis; report which features are used (binary).  
**Phase 2+:** for multi-signal composites, use simple ablations (drop-one feature, re-backtest on val) — more honest than impurity importance on correlated crypto features.

### 3.5 Data quality / trust scores — schema now, numbers honest

**Phase 1 trust model (explicit, not ML):**

```text
trust_score ∈ [0,1] = product of penalties
  completeness, timestamp_monotonic, ohlc_consistency,
  source_class (exchange_native > aggregator > scraped_social),
  history_depth, known_revision_policy
```

| Source class | Base trust |
|--------------|------------|
| Exchange native OHLCV (Binance) | 0.95–0.99 |
| Reputable aggregator OHLCV | 0.80–0.90 |
| Index / fear-greed style | 0.70–0.85 |
| Social sentiment (reconstructed) | 0.40–0.65 |
| Unverified scrape | ≤0.35 |

**Rule:** features below `min_trust` (e.g. 0.7) cannot enter **confirmatory** tests without human override flag in registry.

### 3.6 Automatic literature review — Phase 2 research ops

**Risks:** cost, copyright gray areas, non-reproducible summaries, citation hallucination, idea laundering (“paper says momentum works” → unregistered fishing).

**Phase 1:** `LiteratureRef` optional fields on hypothesis (`url`, `title`, `mapped_taxonomy`, `replication_notes`). Manual entry for the example.  
**Phase 2:** agent with budget, cache, and mandatory human accept before confirmatory registration.

### 3.7 Meta-analysis — the real long-term moat

Agree with external review: after large N, meta-analysis of **the research process** is the advantage.

**Phase 1:** ensure registry schema supports it later:
- `taxonomy`, `feature_tags[]`, `data_sources[]`, `regime_dependence`, `reject_reason_code`, `metrics_json`, `family_id`

**Phase 2+:** SQL queries and a `scripts/meta_report.py` once N ≥ 30–50.

### 3.8 SQLite vs JSON — change adopted

**Decision: SQLite from day one.**

Reasons:
- Queryability (status, sharpe, taxonomy, regime flags).
- Single-file portability, still local-first.
- Append event log table for audit (`hypothesis_events`).
- JSON export remains available for git-friendly snapshots of *candidates only* if desired.

Schema sketch:

```sql
hypotheses(id, version, status, taxonomy, asset, timeframe, spec_json, ...)
runs(id, hypothesis_id, dataset_id, git_sha, config_hash, started_at, ...)
metrics(run_id, split, sharpe, max_dd, n_trades, ...)
events(id, hypothesis_id, ts, from_status, to_status, reason)
data_assets(dataset_id, trust_score, source, sha256, ...)
```

---

## 4. Additional flaws the external review did not emphasize

1. **Overlapping research on one asset:** all ideas share the same BTC path → cross-strategy dependence; “5 independent edges” may be one beta story.  
2. **Survivorship of exchanges:** Binance klines are fine for BTCUSDT; still record venue.  
3. **Lookback burn-in:** SMA(200) daily needs 200 bars before first signal — must align baselines to same effective start.  
4. **Intrabar stops:** Phase 1 should **avoid** stop-loss fills at intrabar extremes unless using conservative adverse fill assumptions; prefer close/next-open rules only.  
5. **Clock and versioning of “today”:** research runs must pass `as_of` timestamp so features don’t accidentally use partial current bar.  
6. **Economic significance vs statistical:** with tiny capital, even a real edge may not clear psychological/operational overhead — track **edge after costs in bps per trade**.  
7. **Adversarial null:** technical rules on prices are overstudied; prior on edge should be skeptical (Bayesian prior at 0 is correct culturally).

---

## 5. Revised Phase 1 scope deltas

### Add to Phase 1 (must)

| Item | Minimal implementation |
|------|------------------------|
| SQLite registry | hypotheses, runs, metrics, events, data_assets |
| Causal regime labels | trend × vol 2×2, past-only |
| Regime-stratified metrics in report | table + concentration warning |
| Block bootstrap + trade-sequence MC | on val always; on test only for candidates |
| Parameter neighborhood sensitivity | small grid on val |
| Data trust_score on manifests | rule-based |
| Confirmatory vs exploratory mode | CLI flag + registry enforcement |
| Primary objective fixed lab-wide | after-cost Sharpe; B&H panel mandatory |
| Excess vs B&H metrics | active return / simple IR |
| Expanding/rolling thresholds only | tested |
| Taxonomy + family_id | schema fields |
| Lockfile | uv or requirements pin |

### Explicitly still Phase 2+

- Automated literature / arXiv / SSRN agent loops  
- Meta-analysis dashboards (script OK when N large)  
- Multi-feature importance / ablation suites  
- Vol-scaled cost models as default  
- Multi-asset, shorting, execution  
- Live X sentiment features  

### Phase 1 “hooks only” (interfaces, no heavy logic)

- `LiteratureRef`  
- `MetaAnalysis` query helpers empty or trivial  
- `FeatureImportance` protocol returning “used features” list  
- xAI client mock  

---

## 6. Revised validation stack (candidate report must include)

1. After-cost performance (full sample splits).  
2. Walk-forward fold table.  
3. Baseline panel (B&H, cash, SMA).  
4. Excess vs B&H.  
5. Regime 2×2 slice.  
6. Block-bootstrap CI + P(mean trade > 0) under skeptical prior.  
7. Monte Carlo path/sequence risk (DD, terminal vs B&H).  
8. Parameter sensitivity / fragility.  
9. 2× cost stress.  
10. Data trust + dataset hash + git + config hashes.  
11. Multiple-testing note (`family_id`, N).  
12. Explicit failure-mode narrative (auto-generated checklist).

---

## 7. Revised success criteria (Phase 1 → Phase 2)

### Process (required) — unchanged spirit, plus:

- [ ] SQLite registry with event audit trail  
- [ ] Regime-stratified report section  
- [ ] Bootstrap/MC module runs deterministically with seed  
- [ ] Exploratory vs confirmatory enforced  
- [ ] Trust scores on data assets  

### Research bar — stricter honesty:

A `candidate` requires untouched **confirmatory** test **and**:

- Primary objective gate on after-cost Sharpe (lab default) **with** block-bootstrap evidence not concentrated on luck  
- MC: not catastrophic sequence risk under stated DD limit (threshold in config)  
- Fragility: not only the exact parameter works  
- Regime report attached (may be regime-specific — allowed if **labeled**, not hidden)  
- family multiple-testing note recorded  

Still true: **zero candidates can be a successful Phase 1.**

---

## 8. What I would cut if schedule slips

Priority order if implementation time is limited:

1. Engine + no-lookahead + costs + splits + registry + one example  
2. WF + baselines + B&H excess  
3. Bootstrap CIs  
4. Regimes in report  
5. MC sequence risk  
6. Sensitivity grid  
7. Trust scores  
8. Everything else  

Never cut: no-lookahead tests, costs, registry audit, reproducibility stamps.

---

## 9. Final skeptical summary

**Strong:** bias controls, promotion ladder, reproducibility, “zero edge is success,” cost stress, modular boundaries.

**Weak / fixed by this review:** JSON registry; incomplete multiple-testing control; full-sample threshold leakage risk; beta masquerading as alpha; i.i.d. bootstrap on dependent trades; metric shopping; premature feature-importance and lit-review agents.

**Philosophy going into code:**  
Build a **small, hostile-to-false-positives** lab. Every dashboard widget must earn its place by changing a reject/pass decision or preventing a lie.

---

*No implementation code in this document. Awaiting approval of revised plan, then Phase 1 build.*
