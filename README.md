# Crypto Research Laboratory (Phase 1)

Personal **research-only** lab for discovering and falsifying BTC/USDT spot trading edges.

**Not a trading bot.** No live keys, no order placement, no leverage, no shorts.

> Finding zero edges is still Phase 1 success.

## Layout

```
src/crl/
  shared/          # data, features, types, config, reproducibility
  research/        # hypotheses, backtest, stats, regimes, reports, journal, pipeline
  production/      # empty execution surface (disabled)
  risk/            # deterministic constraints + promotion gates
  xai/             # mock client + cache + rate limit + cost ledger
configs/           # default fees, gates, splits
examples/          # example hypothesis YAML
journal/           # research journal (human lessons)
docs/              # architecture & skeptical review
```

Research stays messy; production stays boring. They are separated on purpose.

## Quick start

```bash
cd crypto-research-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Offline demo (synthetic data)
crl run -H examples/hyp_sma200_vol_filter.yaml --mock

# Real BTC/USDT daily data (public Binance, no API key)
crl fetch --interval 1d
crl run -H examples/hyp_sma200_vol_filter.yaml

# List registry
crl list
```

Reports land in `reports/`. Registry is SQLite at `registry/crl.sqlite`.  
Journal appends to `journal/RESEARCH_JOURNAL.md`.

## Validation standards (Phase 1)

- Signal on closed bar `t` → position starts bar `t+1` (no look-ahead)
- Causal features only (expanding/rolling — **no full-sample medians**)
- Conservative costs + 2× stress
- Chronological train/val/test + walk-forward on train+val
- Baselines: buy-and-hold, cash, SMA 50/200
- Excess vs buy-and-hold, regime 2×2 slices
- Block bootstrap + trade-sequence Monte Carlo + SMA neighborhood sensitivity
- **Reality Checker** — economic/execution plausibility (human-executable, latency, liquidity, fee fragility, crowding, noise)
- **Single primary metric:** after-cost Sharpe (no metric shopping)
- Exploratory vs confirmatory modes (test set locked until confirmatory; one-shot)

```bash
crl catalog              # write catalog YAMLs → examples/batch/
crl batch                # exploratory evaluate (also updates research_kb/)
crl meta                 # taxonomy survival rates
crl plan                 # evidence-driven research plan (what to test next)
crl learn                # refresh knowledge base + thesis tree from registry
crl thesis               # Research Thesis Tree (mechanism evidence map)
```

Batch results: `reports/batch_summary.md`.  
Research planner: `research_kb/latest_plan.md`, `research_kb/LEARNINGS.md`.  
Thesis tree: `research_kb/THESIS_TREE.md`.  
Persistent CRS role: root `AGENTS.md`.

Rejecting almost all ideas is expected — and healthy. **Plan maximises information gain, not win rate.**

## Example hypothesis

`examples/hyp_sma200_vol_filter.yaml` — long when `close > sma_200` and realized vol below expanding median; exit when `close < sma_200`.

This is a **pipeline vehicle**, not claimed alpha. Rejection is a valid outcome.

## Tests

```bash
pytest -q
```

## Phase ladder

See `docs/PROMOTION_LADDER.md` (authoritative for “when real money?”).

Research lab (Phase 1) → **Signal discovery (Phase 2, current)** → paper → shadow → tiny live  

**Not ready for live trading or paper trading.** Even exploratory `passed_val` is not a buy signal; confirmatory + paper + shadow required before AUD risk.

**Standing orders:** `docs/STANDING_ORDERS.md` — framework frozen; success = evidence quality; never weaken gates.

## Docs

- `docs/PHASE1_PLAN.md` — scope, methodology, success criteria  
- `docs/SKEPTICAL_REVIEW.md` — adversarial architecture review  
- `docs/PHASE1_QUANT_REVIEW.md` — world-class quant self-review + material fixes  

### Post–batch scientific hardening (not feature theater)

- Single PnL identity (trades = bar-net segments)
- Bootstrap of **primary** bar Sharpe (not a parallel trade fantasy)
- Multiple-testing hygiene (family N, DSR/Bonferroni) + confirmatory monthly budget
- Fragility fail-closed; feature matrix cache; data hash verify; frozen registry specs

## Safety

`crl.production.execution.place_order` **always raises** in Phase 1.
