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

- **Closeout of public-rule daily/4h clone wave:** `docs/PHASE2_CLOSEOUT.md` — **0 confirmatory candidates**.  
- **Do not** expand SMA/volume/breakout clone grids.  
- Funding/OI v1 locks closed — do not re-mine without new programme version.  
- **Next research classes (when opened):** flow/whale → X PIT archive → Polymarket (see deferred programme docs).  
- **Parallel:** paper/shadow scaffolding — LIVE hard-disabled until Phase 5 + **no leverage**.  
- Agent notifies human when **close** to small-money autotrading (criteria in closeout §6).

## Live-readiness (Track B) — code may advance; capital may not

| Component | Status |
|-----------|--------|
| Paper broker (sim fills) | Scaffolded |
| Shadow broker (log intents) | Scaffolded |
| LIVE place_order | **Fail-closed** (env+config flags + no exchange adapter) |
| API keys / venue client | Human only |

## Deferred external-signal programmes (do not skip; do not jump the queue)

Softening gates or proxy-laundering social/prediction feeds is **forbidden**.  
Design sketches (not yet executable science batches):

| Programme | Doc |
|-----------|-----|
| Flow / whale / large-player | `docs/PROGRAMME_FLOW_WHALE_V1_DEFERRED.md` |
| X sentiment / attention | `docs/PROGRAMME_X_SENTIMENT_V1_DEFERRED.md` |
| Polymarket event odds | `docs/PROGRAMME_POLYMARKET_V1_DEFERRED.md` |

### X (Twitter) / social

| When | Role |
|------|------|
| **Now** | Deferred design only; OHLCV sentiment_proxy is **not** a substitute for true X |
| **Next research wave** | Versioned PIT archive + lag + pre-reg hyps |
| **Phase 4–5 ops (optional)** | Monitoring only unless a programme has passed gates |

**Harm if early:** look-ahead fiction, non-reproducible scrapes, burned confirmatory budget.

### Polymarket (prediction markets)

| When | Role |
|------|------|
| **Now** | Deferred design only |
| **Next research wave** | Timestamped odds history + as-of join + pre-reg hyps |
| **Never without** | Dataset hash, trust class, frozen gates |

**Harm if early:** sparse/illiquid markets, selection bias, non-reproducible APIs.

### Flow / whale tracking

| When | Role |
|------|------|
| **Now** | Deferred design (`PROGRAMME_FLOW_WHALE_V1_DEFERRED.md`) |
| **Next research wave** | Preferred **before** social if clean PIT flow data is available |
| **Never without** | Publish-time timestamps (when *we* could know), not “wallet later labeled smart” |

### Ordering (do not reorder casually)

1. Finish **P1** (holdout, ledger, artefacts, checkpoints, anchors as planned).  
2. **Funding / OI PIT** (or clean null / impossibility record).  
3. Only then consider **Polymarket** and/or **X historical** as new programmes under the same budget and multiplicity rules.  
4. **Live** social/prediction feeds only after the matching historical programme has honest exploratory evidence — and only under paper/shadow rules before tiny live.
