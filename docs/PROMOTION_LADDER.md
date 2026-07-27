# Promotion ladder — when evidence is strong enough to risk money

**External reviewer posture (adopted):** conservative.  
**Live money:** not until explicitly earned. Grok will never declare “go live” casually.

| Phase | Goal | Exit criteria (approx.) | Status |
|-------|------|-------------------------|--------|
| **1 Research lab** | Honest rejection engine | No look-ahead, WF, costs, registry, reality checks, tests, reproducibility | **Complete** |
| **2 Signal discovery** | Find *candidates* worth paper | Broad families; **quality** hyps; honest rejects; **≥2–3 independent confirmatory survivors from different economic ideas** | **In progress** |
| **3 Paper trading** | Clock-synced sim, no capital | ≥1 month stable; no hidden bugs; fees modeled | Not started |
| **4 Shadow mode** | Live signals, **no orders** | Would-have vs market path logged & reconciled | Not started |
| **5 Tiny live** | System test, not profit hunt | AUD 10–20, spot BTC only, 1 exchange, max 1 trade/day, auto-stop, daily review | **Blocked** |

### External “GO” checklist (AUD 10–20) — all required

**Research**

- [ ] ~300+ well-documented hypotheses (quality-weighted, not clone spam)  
- [ ] Multiple distinct families explored  
- [ ] Standards never weakened  

**Discovery**

- [ ] **2–3 independent confirmatory survivors**  
- [ ] From **different** economic mechanisms (not 3 SMA siblings)  

**Stability (each survivor)**

- [ ] Positive untouched test performance after costs  
- [ ] Robust to higher fees/slippage  
- [ ] Reasonable trade count  
- [ ] No hidden single-regime story (or labeled and accepted consciously)  
- [ ] Economic plausibility intact  

**Paper** — ≥1 month without unexpected failures  

**Shadow** — live signals correct; no exec/timing bugs  

Only then: tiny live as a **system** test, not a profit mandate.

## Hard rules

1. Spectacular backtests alone → **not** go.  
2. Softening gates to create candidates → **forbidden**.  
3. Architecture changes only for scientific correctness / maintainability.  
4. Production `place_order` remains disabled until Phase 5 is explicitly opened.  
5. “Ready for tiny live” is a **human** call after paper + shadow evidence — not a CLI flag.

## Phase 2 current targets

- Expand **distinct** economic mechanisms (not SMA clone spam).  
- Crypto-specific (funding, OI) only with **PIT** series — **done for v1 locks** (funding daily+4h null; OI confirmatory kill). Do not re-mine spent locks.  
- Track survival rates via `crl meta` / Thesis Tree.  
- Confirmatory only after exploratory pass + budget.  
- **Parallel:** paper/shadow **scaffolding** in `src/crl/production/` — LIVE hard-disabled until Phase 5 dual human flags + adapter review.

## Live-readiness (Track B) — code may advance; capital may not

| Component | Status |
|-----------|--------|
| Paper broker (sim fills) | Scaffolded |
| Shadow broker (log intents) | Scaffolded |
| LIVE place_order | **Fail-closed** (env+config flags + no exchange adapter) |
| API keys / venue client | Human only |

## Deferred external-signal programmes (do not skip; do not jump the queue)

These can make the **research base** stronger later. They are **not** reliability infrastructure and **not** current Phase 2 primary work. Primary non-price programme remains **exchange-native funding / OI** (PIT) once P1 integrity lands. Softening gates or proxy-laundering social/prediction feeds is forbidden.

### X (Twitter) / social

| When | Role |
|------|------|
| **Now** | OHLCV **sentiment_proxy** only; live X **not** a backtest feature |
| **Phase 2+ research** | Only with a **versioned, point-in-time historical** archive (paid or frozen snapshot), trust score, lag rules |
| **Phase 4–5 ops (optional)** | Live X as **non-signal** monitoring (outages, regulatory shocks) — never silently fed into untested rules |

**Value if done right:** attention / narrative regime as an *independent* mechanism class after price+funding space is honestly explored.  
**Harm if done early:** look-ahead fiction, non-reproducible “tweets said so,” burned confirmatory budget on untrustworthy series.

### Polymarket (prediction markets)

| When | Role |
|------|------|
| **Now** | **Out of scope** — no pipeline, no hyps, no promotion claims |
| **Phase 2+ research (after funding PIT programme design is locked or blocked)** | Optional bounded programme: crypto-relevant market odds as **market-implied probability / event risk** features, only if history is reconstructible with timestamps and join lag |
| **Never without** | Dataset hash + trust class, pre-registered ≤ small hyp budget, same frozen validation gates |

**Value if done right:** independent event-odds information orthogonal to OHLCV technicals.  
**Harm if done early:** another un-versioned scrape, selection bias on which markets, and distraction from P1 + funding science.

### Ordering (do not reorder casually)

1. Finish **P1** (holdout, ledger, artefacts, checkpoints, anchors as planned).  
2. **Funding / OI PIT** (or clean null / impossibility record).  
3. Only then consider **Polymarket** and/or **X historical** as new programmes under the same budget and multiplicity rules.  
4. **Live** social/prediction feeds only after the matching historical programme has honest exploratory evidence — and only under paper/shadow rules before tiny live.
