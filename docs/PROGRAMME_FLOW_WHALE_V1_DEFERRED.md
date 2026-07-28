# Deferred programme: Flow / whale / “smart money” tracking (v1 design sketch)

**Status:** **Scaffolded (lab-ready)** — see **`docs/PROGRAMME_FLOW_WHALE_V1.md`** + `examples/batch/flow/` + `src/crl/shared/data/flow.py`.  
**Still blocked for science batch:** versioned **real** flow history (human OK for paid APIs). Mock is tests-only.  
This DEFERRED file is a pointer only; binding design is PROGRAMME_FLOW_WHALE_V1.md.

## Scientific question (when opened)

> Do **versioned, lagged** measures of large-player or exchange-flow behaviour support a pre-registered long-only (or flat) rule that survives frozen gates — or is “follow whales” a narrative that fails after costs and multiplicity?

## Agreement with product intent

**Yes, worth exploring later** — as a **new mechanism class**, not a shortcut:

| Agree | Caveat |
|-------|--------|
| Machines can beat humans on bandwidth/discipline | Only with **correct** data timing |
| Whale/flow can be economic (inventory, liquidation, basis) | Public “whale alerts” are often **late, incomplete, or gamed** |
| Aligns with “better than discretionary” ambition | Must not launder look-ahead from Telegram/Twitter dumps |

## Data requirements (binding before any hyp)

1. **Source class** + trust score (exchange ledger, chain analytics vendor, etc.)  
2. **Publish timestamp** of each observation (when *we* could know it)  
3. **As-of join** to decision bars (same discipline as funding/OI)  
4. **Versioned parquet + hash** — no silent revise  
5. **Lag:** signal on closed bar → next open (lab default)  
6. Explicit **non-use** of labels that require future knowledge (e.g. “this wallet later became a winner”)

## Candidate feature families (examples only — lock later)

- Exchange net inflow/outflow (exchange-labeled addresses) as-of t  
- Large transfer count/size z-scores (past-only windows)  
- Open interest + aggressive flow if exchange-native PIT  
- **Not:** “copy trader X’s last 10 trades” without a reproducible archive  

## Multiplicity / budget (when opened)

- ≤ **8–10** pre-registered hyps per programme version  
- No threshold mining on the same flow series after lock  
- Same frozen gates as default config  

## Explicit non-goals

- Live Twitter/Telegram whale bots as unversioned features  
- Claiming that retail “copy trading” APIs are scientific without PIT  
- Leverage / copy-perp risk  

## When to open

After Phase 2 closeout acceptance; **before or instead of** social/Polymarket if flow data with true timestamps is easier to obtain.  
Requires human OK for any **paid** data API keys.
