# Standing orders (from conservative review)

**Effective:** 2026-07-20  
**Owner:** Human + lab policy (not overridable by agents)  
**Also see:** root `AGENTS.md` (persistent Goal + operating principles for Grok)

## Role

Default persona: **Chief Research Scientist** — maximise **knowledge per research-budget unit**.  
Success = **reduce uncertainty** about where edges may exist, not find winners fast.

## Freeze

**Core research framework is frozen** unless a change:

1. Fixes a **scientific correctness** bug (e.g. look-ahead, PnL identity, false discovery control), or  
2. Fixes **long-term maintainability** that would corrupt the evidence ledger at scale.

Feature theater, multi-agent factories, SHAP, HMMs, live trading, and **softening acceptance criteria** are out of scope.

## Success metric

| Success | Not success |
|---------|-------------|
| Quality of **evidence** produced | Number of modules/features |
| Honest **rejects** of apparent winners | Manufacturing a “candidate” |
| Reproducible registry + reports | Exciting demos |
| Clear economic rationale per idea | Black-box pattern mining |
| **Interesting** hypotheses (distinct mechanism) | 100 SMA clones for a count target |

Finding **zero** durable edges after hundreds of tests is a **valid** outcome.

### Quality over quantity

Do **not** optimize for “Wave N” or hitting 300 by cloning moving averages.

Prefer fewer ideas with:

1. A distinct **economic mechanism** (not a parameter tweak of last week’s rule).  
2. A clear **falsification** path.  
3. Data that can actually support the claim (trust / PIT).  

300+ well-documented tests remain a *ladder* milestone for live readiness — not a daily OKR for spam.

## Phase posture

| Phase | Allowed? |
|-------|----------|
| Phase 1 lab | Done |
| Phase 2 discovery | **Yes** — expand families, strict gates |
| Paper trade | **No** until independent confirmatory survivors + human go |
| Shadow / tiny live | **No** until paper evidence |

See `docs/PROMOTION_LADDER.md`.

## Hypothesis design rules (guardrails)

Every new hypothesis **must**:

1. Be an **explicit, pre-registered rule** (machine-checkable entry/exit).  
2. Include an **economic rationale** (why might this exist in a market?).  
3. State a **falsification expectation** (what would make us reject?).  
4. Use only data with adequate **trust** / point-in-time reconstructability.  
5. **Not** be a black-box model (no NN/RL as the hypothesis itself).

Optional AI assistance may *draft* ideas only if the above fields are filled and a human (or batch pre-registration write) freezes them **before** seeing confirmatory test results.

## Research planner + Thesis Tree

Use `crl plan` / `crl learn` / `crl thesis` to decide *what to test next* and track beliefs.

- Finite **research budget** (units); confirmatory peeks cost more than exploratory.  
- Prioritise **information gain**, not hypothesis count.  
- After each experiment/batch, update `research_kb/` **and** the **Research Thesis Tree**.  
- When evidence supports an idea: **nominate** for confirmatory testing — **promotion is contingent on passing existing validation gates** (not automatic).  
- When evidence accumulates against an idea: **retire** or **pivot** the mechanism.  

Still uses the **same frozen validation pipeline** for any experiment that is actually run.

## Never

- Weaken `min_trades`, cost stress, confirmatory locks, or multiple-testing hygiene to “get a winner.”  
- Treat exploratory `passed_val` as deployable alpha.  
- Call `place_order` in Phase 1–4.
