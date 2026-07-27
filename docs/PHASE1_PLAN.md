# Crypto Research Laboratory — Phase 1 Plan

**Status:** Revised after skeptical quant review — awaiting approval before implementation  
**Mode:** Research-only (no execution, no live keys, no order placement)  
**Asset scope:** BTC/USDT spot only  
**Decision frequency:** 4h or daily candles  
**Capital context:** Tiny (10–50 AUD) — design for realism and robustness, not HFT  

**Related:** `docs/SKEPTICAL_REVIEW.md` (weaknesses, rejections of premature features, schema deltas)

### Revision highlights (post external + self review)

| Change | Decision |
|--------|----------|
| Registry | **SQLite** (not JSON files) + event audit table |
| Monte Carlo | **Phase 1** for candidates: block bootstrap + trade-sequence risk |
| Regimes | **Phase 1** causal trend×vol 2×2 labels + stratified reports |
| Bayesian confidence | **Pragmatic:** bootstrap + skeptical prior on mean trade return |
| Feature importance | **Hooks only** Phase 1; ablations in Phase 2+ |
| Data trust scores | **Phase 1** rule-based on manifests |
| Literature agent | **Phase 2**; Phase 1 optional `LiteratureRef` fields |
| Meta-analysis | **Schema hooks** Phase 1; queries when N is large |
| Primary objective | Lab-wide **after-cost Sharpe** (no metric shopping) |
| Exploratory vs confirmatory | Enforced in CLI + registry |

---

## 1. Mission

Build an autonomous **personal AI Crypto Research Laboratory** whose primary job is to:

1. Generate precise, falsifiable trading hypotheses.
2. Validate them with scientific rigor (no look-ahead, realistic costs, proper OOS).
3. Register every idea with results, rejection reasons, and lessons.
4. Rank and reject weak ideas so only robust edges survive.

Trading execution is **out of scope** until later phases. Optimize for **risk-adjusted performance after costs**, regime stability, and true out-of-sample predictive power — not raw returns.

---

## 2. Proposed Architecture

### 2.1 Design principles

| Principle | Implication |
|-----------|-------------|
| **Research > execution** | No broker adapters, no order routers in Phase 1 |
| **Falsifiability first** | Every hypothesis is a machine-readable rule set with pass/fail criteria |
| **Bias control by construction** | Point-in-time data, closed-bar signals only, frozen datasets |
| **Reproducibility** | Dataset hashes, config snapshots, code git SHA, run timestamps |
| **Agent-safe risk** | Deterministic risk module; agents propose, they do not override risk |
| **Modular interfaces** | Swap data providers, cost models, stats engines without rewrite |
| **Cost-aware AI** | xAI/search clients with cache, rate limits, token/cost ledger |

### 2.2 Logical architecture (layers)

```
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATION (CLI / scripts)                                  │
│  run_pipeline · generate_hypothesis · backtest · report · rank  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  HYPOTHESIS LAYER                                               │
│  schema · generator (rules + optional LLM) · registry · ranker  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  VALIDATION / BACKTEST LAYER                                    │
│  splitter · engine · baselines · costs · stats · walk-forward   │
│  regimes · monte_carlo · sensitivity                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  DATA LAYER                                                     │
│  fetchers · store · features · point-in-time · versioning       │
│  trust_score                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  SHARED KERNEL                                                  │
│  config · types · logging · reproducibility · xai client stubs  │
│  risk (deterministic gates) · promotion policy                  │
│  research modes: exploratory | confirmatory                     │
└─────────────────────────────────────────────────────────────────┘
```

**Data flow (single hypothesis end-to-end):**

```
HypothesisSpec (taxonomy, family_id, primary_objective locked)
    → Registry.create(status=draft)  # SQLite
    → DataLayer.load(dataset_id, trust_score, bars closed as of t)
    → FeatureBuilder (rolling/expanding thresholds only)
    → RegimeLabeler (causal trend × vol)
    → mode=exploratory?  → train/val + WF only (test locked)
    → mode=confirmatory? → requires frozen spec hash; test once
    → BacktestEngine + CostModel + Baselines + excess vs B&H
    → StatsEngine (block bootstrap, MC sequence risk, sensitivity)
    → Ranker + RejectionRules (single primary metric + constraints)
    → Registry.events + metrics tables
    → ReportWriter (md + json; regime table; failure modes)
```

### 2.3 Component responsibilities

#### A. Hypothesis Generator
- **Input:** Market regime summaries, feature catalog, registry history (what failed), optional LLM prompts via `xai` client.
- **Output:** `HypothesisSpec` JSON (see schema below) — never free-text-only “ideas.”
- **Phase 1 mode:** Template/rule-based generator + one hand-authored example; LLM optional behind interface (offline mock OK).

#### B. Data Layer
- Fetch and cache OHLCV for BTC/USDT (4h + 1d).
- Compute derived features: returns, realized vol, volume z-scores, simple MAs, ATR.
- Optional experimental signal: **only if historically reconstructible** (default Phase 1: **omit live X sentiment** unless a frozen historical snapshot exists; use a *proxy* or stub interface instead).
- Store as versioned parquet + manifest (`dataset_id`, source, time range, hash).

#### C. Backtesting Engine
- Bar-based, closed-candle only: signal on bar `t` executes at open of `t+1` (or next available open) — configurable, default conservative.
- Long-only BTC/USDT spot; cash or BTC inventory; no leverage, no shorts.
- Cost model: fee + half-spread + slippage (bps), configurable, conservative defaults.
- Equity curve, drawdowns, turnover, trade list.

#### D. Hypothesis Registry (SQLite)
- Local SQLite DB (`registry/crl.sqlite`) with tables: `hypotheses`, `runs`, `metrics`, `events`, `data_assets`.
- Append-only `events` audit trail (status transitions + reasons).
- Queryable for meta-analysis later (`taxonomy`, `family_id`, Sharpe, regime flags, reject codes).
- Optional JSON export of candidates only (git-friendly snapshots), not the primary store.

#### E. Reporting
- Per-run markdown report + machine-readable JSON.
- Explicit section: **failure modes observed** (overfit, regime-specific, fee-sensitive, etc.).

#### F. Risk Module (deterministic, non-overridable)
- Even in research: max position = 100% long or 0% cash; max trades/year; min hold bars; kill if cost assumptions violated.
- Promotion gates as pure functions of metrics (no agent override path).

#### G. xAI / Grok Integration Interface (stubs + design)
- `XAIClient` protocol: `search_x`, `search_web`, `complete` with:
  - disk cache (keyed by request hash)
  - rate limiter
  - cost ledger (estimated tokens / calls)
  - dry-run / mock mode for CI
- **No** unlimited-call assumptions; budgets in config.

### 2.4 Core schemas (conceptual)

**HypothesisSpec (required fields):**
```yaml
id: hyp_YYYYMMDD_slug
version: 1
asset: BTC/USDT
timeframe: 4h | 1d
direction: long_only
entry:  # precise, falsifiable
  type: rule
  expression: "close > sma_200 and vol_z_20 > 1.0"  # or structured AST
exit:
  type: rule | hold_bars | stop_take
  expression: "..."
position_sizing: full | fixed_fraction  # Phase 1: full or 0
rationale: string
falsification_criteria:
  min_oos_sharpe_after_costs: 0.3   # example thresholds live in config
  max_oos_drawdown: 0.45
  min_trades: 30
  beat_buy_hold: true | risk_adjusted_only
data_requirements: [ohlcv, realized_vol]
created_at: ISO8601
code_sha: ...
dataset_id: ...
```

**Registry statuses:** `draft → running → passed_train → failed_val | passed_val → failed_test | candidate → rejected | archived`

---

## 3. File Structure

```
crypto-research-lab/
├── README.md
├── pyproject.toml                 # deps, package metadata
├── .env.example                   # no secrets required for Phase 1 core
├── .gitignore
├── configs/
│   ├── default.yaml               # fees, periods, thresholds
│   ├── costs_conservative.yaml
│   └── promotion_gates.yaml
├── docs/
│   ├── PHASE1_PLAN.md             # this document
│   ├── VALIDATION.md              # methodology detail
│   └── DATA_SOURCES.md
├── src/
│   └── crl/                       # crypto research lab package
│       ├── __init__.py
│       ├── cli.py                 # entrypoints
│       ├── config.py
│       ├── types.py               # shared dataclasses / pydantic models
│       ├── data/
│       │   ├── __init__.py
│       │   ├── sources/
│       │   │   ├── base.py
│       │   │   ├── binance_public.py
│       │   │   └── mock.py
│       │   ├── store.py           # parquet cache + manifests
│       │   ├── features.py
│       │   ├── trust.py           # rule-based trust scores
│       │   └── versioning.py
│       ├── hypotheses/
│       │   ├── __init__.py
│       │   ├── schema.py
│       │   ├── generator.py       # rule templates + optional LLM
│       │   ├── registry.py        # SQLite
│       │   ├── ranker.py
│       │   └── taxonomy.py
│       ├── backtest/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── costs.py
│       │   ├── baselines.py
│       │   ├── splitter.py        # train/val/test + walk-forward
│       │   └── metrics.py
│       ├── stats/
│       │   ├── __init__.py
│       │   ├── significance.py      # block bootstrap, skeptical prior
│       │   ├── monte_carlo.py       # trade-sequence / path risk
│       │   ├── sensitivity.py       # parameter neighborhood
│       │   └── multiple_testing.py
│       ├── regimes/
│       │   ├── __init__.py
│       │   └── labels.py            # causal trend × vol 2×2
│       ├── risk/
│       │   ├── __init__.py
│       │   ├── constraints.py     # deterministic, non-overridable
│       │   └── promotion.py
│       ├── reporting/
│       │   ├── __init__.py
│       │   └── report.py
│       ├── xai/
│       │   ├── __init__.py
│       │   ├── client.py          # protocol + mock + real stub
│       │   ├── cache.py
│       │   ├── ratelimit.py
│       │   └── cost_ledger.py
│       └── pipeline/
│           ├── __init__.py
│           └── run.py             # end-to-end orchestration
├── data/                          # gitignored raw/processed (manifests may be tracked)
│   ├── raw/
│   ├── processed/
│   └── manifests/
├── registry/                      # crl.sqlite (+ optional JSON exports)
│   └── exports/
├── reports/                       # generated run reports
├── examples/
│   └── hyp_sma_trend_filter.yaml  # first end-to-end example
├── tests/
│   ├── test_no_lookahead.py
│   ├── test_costs.py
│   ├── test_splitter.py
│   ├── test_registry.py
│   ├── test_engine_reproducibility.py
│   └── fixtures/
└── scripts/
    ├── fetch_btc_usdt.py
    ├── run_example_hypothesis.py
    └── rank_registry.py
```

**Dependency philosophy:** Python 3.11+, `pandas`, `numpy`, `pyarrow`, `pydantic`, `pyyaml`, `httpx`, `pytest`. Avoid heavy ML stacks in Phase 1. Optional: `statsmodels` for HAC/Newey–West if needed.

---

## 4. Phase 1 Scope

### 4.1 In scope (build now)

| Item | Detail |
|------|--------|
| Modular package + CLI | Installable `crl`, config-driven |
| BTC/USDT OHLCV fetch | Public Binance (or equivalent) spot klines, 4h + 1d |
| Versioned data store | Parquet + SHA256 manifest |
| Feature set v1 | Returns, SMA, EMA, realized vol, ATR, volume z-score |
| Hypothesis schema + **SQLite registry** | Lifecycle, events audit, taxonomy, family_id |
| Rule-based signal evaluation | Declarative rules on closed bars; rolling/expanding thresholds only |
| Backtest engine | Long-only, next-open fill, costs, equity curve; no intrabar stops in v1 |
| Cost model | Fee + spread + slippage (bps) + 2× stress |
| Baselines + excess vs B&H | B&H, cash, SMA cross; active return / simple IR vs B&H |
| Split + walk-forward | Chronological train/val/test; rolling WF windows |
| **Exploratory vs confirmatory** | Test set locked until confirmatory; one-shot per version |
| Regime labels + stratified metrics | Causal trend×vol 2×2; concentration warning |
| Stats | After-cost Sharpe (primary), block bootstrap CI, skeptical P(mean trade>0) |
| Monte Carlo (candidates) | Trade-sequence / block resampling → DD & terminal risk |
| Parameter sensitivity | Small neighborhood on val; fragility note |
| Data trust scores | Rule-based on source class + integrity checks |
| Ranker + rejector | Single primary objective + hard constraints (no metric shopping) |
| Reports | Markdown + JSON; regime table; MC; failure modes |
| Risk module | Deterministic constraints + promotion gate functions |
| xAI client interface | Mock + cache + rate limit + cost ledger stubs |
| Schema hooks for Phase 2 | LiteratureRef, meta-analysis fields, feature list |
| One complete example | Full hypothesis → backtest → registry → report |
| Unit tests | Look-ahead, full-sample quantile ban, costs, splits, registry modes |
| Lockfile | Pinned deps for reproducibility |

### 4.2 Deliberately out of scope (Phase 1)

| Out | Why |
|-----|-----|
| Live trading / paper order placement | Phase 3+ |
| API keys for exchanges (trading) | Not needed; public market data only |
| Leverage, shorts, futures, options | Constraints |
| Multi-asset / portfolio construction | Later |
| HFT / tick / L2 order book | Frequency mismatch; capital tiny |
| Live X sentiment as primary signal | Historical reconstructability risk (see §5) |
| Auto-ML / neural nets / RL agents | Overfit magnet at this capital/data scale |
| SHAP / multi-signal feature importance theater | Single-rule Phase 1; ablations later |
| Automated literature / arXiv agent loops | Phase 2 research ops (cost + hallucination risk) |
| Full meta-analysis product | Needs N≫1; schema ready in Phase 1 |
| Intrabar stop fills without adverse assumptions | Avoid false precision |
| Real-money risk sizing beyond full/flat | Later |
| Dashboard UI | Reports + CLI sufficient |
| Cloud deployment | Local-first research lab |
| Agent autonomy loops that spend unbounded API $ | Budgeted stubs only |

### 4.3 Phase ladder (promotion gates — documented now, enforced later)

```
Phase 1 Research (historical + OOS walk-forward)
    → Phase 2 Expanded research (more hyps, stronger stats, optional frozen alt-data)
    → Phase 3 Paper / simulated live (clock-synced, no capital)
    → Phase 4 Shadow mode (signals logged vs market, still no orders)
    → Phase 5 Tiny live (hard-capped AUD, human kill-switch)
```

Each gate is a **pure function** of metrics + time-in-status + failure history. Agents cannot bypass.

---

## 5. Data Sources — Feasibility & Costs

### 5.1 Primary: Exchange public OHLCV (recommended)

| Source | Use | Cost | Notes |
|--------|-----|------|-------|
| **Binance public REST** `/api/v3/klines` | BTCUSDT spot OHLCV | **Free** | Excellent for spot BTCUSDT; well-documented intervals (4h, 1d); rate limits apply (~1200 weight/min tier-dependent). No API key required for public klines. |
| Binance Vision data dumps | Bulk historical | **Free** | Good for reproducibility snapshots; larger download. |

**Feasibility:** High. Best Phase 1 default for timestamp-correct spot candles.

**Mitigations:** Local cache; respect rate limits; store full response metadata; never re-fetch silently mid-experiment (pin `dataset_id`).

### 5.2 Aggregators (secondary / optional)

| Source | Cost | Caveat |
|--------|------|--------|
| CoinGecko Demo API | Free tier | Historical depth often **limited** (e.g. ~365 days on free); paid for full history. Aggregated prices ≠ single-exchange executable. |
| CoinGecko Pro | Paid | Better history; still aggregator — prefer exchange for execution-realism later. |
| CryptoCompare / others | Free–paid | Same aggregation caveats. |

**Phase 1 policy:** Prefer **Binance spot klines** for BTC/USDT. Use aggregators only for cross-checks or non-OHLCV metadata.

### 5.3 Experimental: X / social sentiment

| Approach | Backtestable? | Phase 1 |
|----------|---------------|---------|
| Live X Search via xAI | **No** (not historical) | Interface only |
| Paid historical social datasets | Sometimes, costly | Out unless budgeted |
| Frozen offline snapshot (if obtained) | Yes, if timestamps clean | Optional later |
| **Proxy:** volume/vol regime labels | Yes | Preferred experimental “sentiment stand-in” |

**Policy:** Do not claim a sentiment edge without a versioned, point-in-time historical series. Ship `xai` client for *hypothesis ideation* and *literature-style search*, not as a fake OHLCV feature.

**Later placement (do not forget):** a true X/social programme is **Phase 2+ research**, after P1 and after or alongside the funding/OI PIT path — never as a reliability patch. Optional **ops-only** live X monitoring is Phase 4–5, not a signal. Full gate table: `docs/PROMOTION_LADDER.md` § Deferred external-signal programmes.

### 5.3b Deferred: Polymarket / prediction markets

| Approach | Backtestable? | Phase 1 |
|----------|---------------|---------|
| Live Polymarket scrape as feature | **No** (no sealed history in lab) | **Out** |
| Versioned historical odds + event join | Yes, if timestamps + lag clean | **Out** (future programme) |
| Using odds without trust/PIT | Fiction | Forbidden |

**Policy:** Polymarket is **not** part of Phase 1 and is **not** a shortcut to autotrading reliability. If pursued later, treat as a **bounded Phase 2+ mechanism programme** (market-implied event risk), only with hashed PIT series, explicit join lag, small pre-registered hyp budget, and the same frozen gates. Ordering: after funding/OI design is locked or blocked — see promotion ladder deferred programmes.

### 5.4 Cost summary (Phase 1)

| Item | Expected cost |
|------|----------------|
| OHLCV data | $0 (public Binance) |
| Compute | Local laptop CPU |
| xAI API (optional ideation) | User-controlled; default **mock/off** |
| Storage | <1 GB for years of 4h/1d BTC |

---

## 6. Major Failure Modes & Mitigations

| Failure mode | How it appears | Mitigation in design |
|--------------|----------------|----------------------|
| **Look-ahead bias** | Using bar close features to trade same bar | Signal on closed bar `t` → fill at open `t+1`; unit tests |
| **Data leakage** | Scaling/features fit on full sample | Fit transforms **inside** train fold only; pipeline enforces |
| **Survivorship bias** | Testing delisted alts only | Phase 1: BTC only — largely N/A |
| **Overfitting / p-hacking** | Mining many rules until one “works” | Registry logs **all** tests; multiple-testing adjustment; limited hypothesis budget per week; pre-registered falsification criteria |
| **Repeated-testing bias** | Reusing same test set | Strict: one untouched test per hypothesis version; new version requires new pre-registration; WF uses rolling val, final test once |
| **Regime overfit** | Edge only in 2020–21 bull | Multi-window WF; report per-regime slices (bull/bear/sideways via simple trend labels) |
| **Cost blindness** | Gross Sharpe looks good | Always report **after** fees/spread/slippage; stress +2× costs |
| **Low sample size** | 5 trades look lucky | `min_trades` gate; bootstrap CIs; prefer daily/4h multi-year |
| **Non-reproducibility** | Different numbers next week | Dataset hash, config dump, code SHA, seed, frozen parquet |
| **Agent overrides risk** | Future LLM “increases size” | Risk module has no write path from agents; promotion is code not prompt |
| **Sentiment fiction** | Backtest uses future tweets | Sentiment experimental only with frozen PIT data; else excluded |
| **Execution fantasy** | Assuming mid-price fills | Conservative next-open + bps costs |
| **Selection bias in reporting** | Only show winners | Ranker lists rejects; registry is append-only |

---

## 7. Exact Validation Methodology

### 7.1 Data hygiene

1. Download OHLCV; drop incomplete open candle.
2. Validate monotonic timestamps, no duplicates, OHLC consistency (`low ≤ open/close ≤ high`).
3. Persist parquet; write manifest: `source`, `symbol`, `interval`, `start`, `end`, `row_count`, `sha256`, `fetched_at`.
4. All experiments reference `dataset_id` only (not “latest”).

### 7.2 Chronological splits (default)

For multi-year 4h or daily data (illustrative; exact dates in config):

| Split | Role | Approx. share | Rule |
|-------|------|---------------|------|
| **Train** | Rule development / param grid (bounded) | ~50% | Oldest |
| **Validation** | Model selection, early reject | ~25% | Middle |
| **Test** | **Untouched** final evaluation | ~25% | Newest |

- **No random shuffles.**  
- **No peeking at test** during generation or tuning.  
- Hypothesis version is frozen before test evaluation.

### 7.3 Walk-forward (primary robustness check)

1. Choose train window length `W_train`, val length `W_val`, step `S`.
2. For each fold `i`: fit allowed params on train only → evaluate on following val.
3. Aggregate OOS val metrics across folds (mean, median, % positive folds).
4. **Only if** WF val passes gates → run **once** on held-out test.

Default starting point (daily): e.g. 2y train / 6m val / step 3m (config-tunable).  
4h: scale windows by bar count equivalently.

### 7.4 Execution assumptions (locked for Phase 1)

- **Signal time:** end of bar `t` (all features use data ≤ `t` close).  
- **Order:** marketable long or flat only.  
- **Fill:** open of bar `t+1`.  
- **Position:** 0% or 100% of equity in BTC (or fixed fraction config).  
- **Costs per round-trip (defaults, conservative):**
  - Fee: 10 bps per side (0.10%) — worse than top-tier VIP
  - Half-spread: 1–2 bps
  - Slippage: 5 bps per side
  - **Stress:** 2× total cost scenario must still clear a weaker gate

### 7.5 Baselines (mandatory comparison)

1. **Buy-and-hold BTC** (same period, same cost on initial entry only or zero ongoing — report both).  
2. **Always cash** (0 return, 0 vol).  
3. **Simple SMA crossover** (e.g. 50/200 daily) as dumb technical baseline.

A hypothesis “wins” only if it improves **risk-adjusted after-cost** metrics vs buy-and-hold *or* delivers materially lower drawdown with competitive CAGR — thresholds in config, not vibes.

### 7.6 Metrics (computed after costs)

| Metric | Purpose |
|--------|---------|
| **After-cost Sharpe (primary objective, lab-wide)** | Pass/fail driver — no shopping |
| CAGR / total return | Magnitude (diagnostic) |
| Volatility (ann.) | Scale |
| Sortino / Calmar | Downside diagnostics |
| Max drawdown + time underwater | Path risk (constraint) |
| **Excess vs B&H** (active return, simple IR) | Avoid beta cosplay |
| Turnover / # trades / avg hold / edge bps | Cost & sample diagnostics |
| Avg trade return + **effective N** note | Dependence-aware sample size |
| % winning folds (WF) | Stability |
| **Block-bootstrap** 95% CI on Sharpe / mean trade | Uncertainty (not i.i.d.) |
| **P(mean trade return > 0)** under skeptical prior | Pragmatic “confidence” |
| **MC sequence risk** | Fraction of resamples with DD breach / underperform B&H |
| **Fragility index** | % of param neighbors that still pass val gates |
| Regime 2×2 metrics + concentration | Where the edge (if any) lives |
| Family N + Deflated Sharpe / Bonferroni note | Multiple testing |

### 7.6b Regime labeling (causal)

- Trend: close vs SMA(200) using past data only.  
- Vol: realized vol vs **expanding** median (not full-sample).  
- Report metrics per bull-low / bull-high / bear-low / bear-high.  
- Warn if >80% of excess return sits in one cell (label, don’t hide).

### 7.7 Statistical decision rules (Phase 1 gates)

**Single primary objective:** after-cost Sharpe (lab default). Secondary metrics **cannot alone** flip reject → pass.

A hypothesis is **rejected** unless **all** hold on validation (WF) and, if confirmatory, on test:

1. `n_trades ≥ min_trades` (default 30 daily) **and** report effective-N caveat.  
2. Primary: after-cost Sharpe clears `sharpe_min` **and** block-bootstrap evidence is not pure luck (e.g. CI or skeptical P(mean>0) per config).  
3. WF stability: ≥60% folds non-negative excess vs cash (config).  
4. Max DD constraint (absolute and/or vs B&H — config); not an alternate primary objective.  
5. 2× cost stress: primary metric does not collapse below floor.  
6. Overfit gap: train Sharpe − test Sharpe ≤ `overfit_gap`.  
7. Confirmatory only: MC sequence risk within configured DD/terminal bounds; fragility not “single point in param space.”  
8. Data assets used have `trust_score ≥ min_trust` (default 0.7).

**Passed candidates** → status `candidate` with full report — **not** live.

### 7.8 Multiple-testing policy

- Registry is the audit log of family-wise testing (`family_id`, taxonomy).  
- Cap confirmatory tests per month / per taxonomy (config research budget).  
- Exploratory mode: **cannot** write test metrics for promotion.  
- After test is run on a version: **immutable**; edits require new version + new budget unit.  
- Report naive Sharpe **and** family-size penalty note (Deflated Sharpe or Bonferroni).

### 7.9 Reproducibility checklist (every run)

- `git_sha`, dirty flag  
- `config` snapshot hash  
- `dataset_id` + data hash  
- `hypothesis_id` + version  
- `python` version, dependency lock (optional `uv.lock` / `requirements.txt`)  
- RNG seed if any stochastic step (bootstrap)

---

## 8. Ordered Implementation Sequence

| Step | Deliverable | Exit criteria |
|------|-------------|---------------|
| **0** | Repo skeleton, `pyproject.toml`, configs, README | `pip install -e .` works |
| **1** | Types + config loader + logging | Unit tests green |
| **2** | Data source (Binance public) + store + manifest | Can fetch & pin BTCUSDT 1d/4h |
| **3** | Feature builder + look-ahead tests | Tests prove no future peek |
| **4** | Cost model + baselines | Known hand-calculated trade matches engine |
| **5** | Backtest engine (long-only, next-open) | Equity curve for buy-hold matches reference |
| **6** | Splitter + walk-forward | Deterministic fold boundaries |
| **7** | Metrics + block bootstrap + skeptical confidence | Seeded, deterministic |
| **8** | Regime labels + stratified metrics | Causal; unit-tested no full-sample median |
| **9** | Monte Carlo sequence risk + param sensitivity | Candidate path only OK |
| **10** | Hypothesis schema + **SQLite registry** + exploratory/confirmatory | CRUD, events, test lock |
| **11** | Ranker + rejection + risk/promotion (single primary metric) | Gates unit-tested |
| **12** | Reporting (md + json) full diagnostic stack | Human-readable failure modes |
| **13** | Pipeline orchestration CLI | One command runs full path |
| **14** | xAI client stubs (cache, rate limit, ledger, mock) | Tests pass offline |
| **15** | **Example hypothesis E2E** | Registry row + report sample |
| **16** | Docs polish + Phase 2 gate checklist | Ready for review |

**If schedule slips, never cut:** no-lookahead tests, costs, registry audit, reproducibility stamps. Cut order: sensitivity → MC → regimes polish → trust scores → xAI polish.

**First example hypothesis (proposed):**  
**“BTC daily: long only when close > SMA(200) and 20-day realized vol below its median; exit when close < SMA(200).”**  
Classic, falsifiable, enough trades over years, good vehicle to prove the pipeline — not expected to be a holy grail.

---

## 9. Measurable Success Criteria → Phase 2

Phase 1 is **successful** when **all** process criteria are met, and **ideally** one research criterion:

### 9.1 Process criteria (required)

- [ ] End-to-end pipeline runs offline after one data fetch.  
- [ ] SQLite registry with event audit trail; schema-valid rows + reject/pass reasons.  
- [ ] Exploratory vs confirmatory enforced (test locked appropriately).  
- [ ] Look-ahead unit tests pass; fill model is next-open; no full-sample quantiles.  
- [ ] Costs applied and 2× stress-tested.  
- [ ] Train/val/test + walk-forward implemented and documented.  
- [ ] Buy-and-hold + SMA baselines + **excess vs B&H** automatic.  
- [ ] Regime-stratified section in reports.  
- [ ] Block bootstrap (+ MC on candidate path) deterministic with seed.  
- [ ] Data trust scores on manifests.  
- [ ] Reproducibility stamps (dataset, config, git, deps lock) on reports.  
- [ ] Risk/promotion modules are deterministic pure functions; single primary metric.  
- [ ] xAI interface exists with mock mode (no mandatory paid calls).  
- [ ] One complete example hypothesis fully executed and stored.

### 9.2 Research criteria (justify Phase 2 expansion)

**Minimum bar to expand research capacity (Phase 2):**

1. Pipeline has evaluated ≥ 5 distinct pre-registered hypotheses (including rejects).  
2. **At least one** hypothesis on untouched **confirmatory** test (after costs):
   - Clears primary after-cost Sharpe gate with block-bootstrap / skeptical-confidence support; **and**
   - `n_trades ≥ min_trades`; **and**
   - Passes 2× cost stress; **and**
   - Overfit gap within limit; **and**
   - WF: majority of folds non-negative excess return vs cash; **and**
   - MC sequence risk within config; **and**
   - Fragility not single-point; **and**
   - Regime report attached (regime-specific edges allowed if **labeled**).  
3. Marked `candidate` with remaining risks listed — not “proven profitable.”  
4. Family multiple-testing note recorded.

**If no hypothesis passes:** Phase 1 is still a **systems success** if process criteria hold — the correct outcome is “no edge found yet,” not forced discovery. Phase 2 then focuses on better hypothesis classes, meta-analysis, literature ops — **not** live trading.

### 9.3 Explicit non-criteria (do not use these to “win”)

- Highest raw return on train  
- Single magic backtest screenshot  
- Unregistered parameter fishing  
- Sentiment stories without PIT data  

---

## 10. Safety & Governance (research mode)

- No exchange trading keys in repo or configs.  
- `.env.example` only for optional xAI research keys later.  
- Append-only registry semantics (corrections = new events).  
- Human approval required before any future phase that touches capital.  
- Default CLI paths cannot place orders (no such code paths in Phase 1).

---

## 11. What I will implement after your approval

1. Full Phase 1 package structure as above.  
2. Working data → features → backtest → WF → stats → registry → report pipeline.  
3. **One** complete example hypothesis with real historical BTC/USDT data, backtest, and registry entry.  
4. Tests for look-ahead, costs, reproducibility.  
5. Short README: how to run the example.

**I will not** implement multi-asset systems, live trading, or unbounded agent loops until you approve later phases.

---

## 12. Open decisions for you (optional feedback)

1. **Default timeframe:** daily vs 4h for the first example? (Recommendation: **daily**.)  
2. **Data source:** confirm Binance public BTCUSDT as canonical. (Recommendation: **yes**.)  
3. **Registry backend:** **SQLite** (decided in revision; confirm).  
4. **xAI:** mock-only for first merge, or wire real API behind env flag? (Recommendation: **mock-only**.)  
5. **Lab primary metric:** after-cost Sharpe (recommended) vs Calmar?

---

## 13. Response to external review (summary)

Agreed and integrated: Monte Carlo (disciplined), regimes, pragmatic confidence, data trust scores, SQLite, meta-analysis schema hooks, literature as Phase 2.

Pushed back / deferred: feature-importance percentages for single-rule systems; automated weekly lit agents before reproducibility core exists; treating every diagnostic metric as a pass key.

**Strongest line remains:** finding zero edges is still Phase 1 success.

---

*End of revised Phase 1 plan. See `docs/SKEPTICAL_REVIEW.md` for full adversarial critique. No substantial implementation code until approval.*
