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

- Expand pre-registered catalog in waves (trend, mom, vol, volume, calendar, structure).  
- Crypto-specific (funding, OI) only with **PIT historical series** + trust scores — no proxy laundering.  
- Track survival rates via `crl meta`.  
- Confirmatory runs only after exploratory pass + budget.
