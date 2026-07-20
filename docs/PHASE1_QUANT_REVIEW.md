# Phase 1 Quant Self-Review (Jane Street / RenTech style)

**Date:** 2026-07-20  
**Scope:** What a skeptical shop would flag *before* scaling hypothesis volume.

## Material weaknesses found (and fixed)

| # | Flaw | Fix |
|---|------|-----|
| 1 | Multiple-testing labeled not controlled | Family N + Bonferroni / Deflated Sharpe hygiene; confirmatory monthly budget enforced |
| 2 | Bootstrap on trade Sharpe ≠ primary metric | Bootstrap **bar after-cost Sharpe** with real annualization |
| 3 | Equity path ≠ trade PnL | Single identity: trades = prod of bar nets on long segments; open-to-open gross |
| 4 | Fragility fail-open for non-SMA | Fail-closed (`pass_frac=None`); numeric threshold neighborhoods; confirmatory hard-requires |
| 5 | Registry rewrite on re-run | Frozen `(id,version)` after non-draft; hash lock |
| 6 | No data re-hash on load | `load_dataset(verify_hash=True)` |
| 7 | Feature rebuild per hyp | Feature store cache `dataset_id + schema_version` |
| 8 | YAML `365 * 6` was a string | Numeric `2190` + safe parser |

## What we deliberately did NOT add

- Multi-agent LLM factories  
- SHAP dashboards  
- HMM regimes  
- Live trading  
- Softening `min_trades`  

## Philosophy

> Only propose additions if they materially improve scientific correctness or long-term maintainability.

Complexity is earned. The lab remains a **rejection engine**.
