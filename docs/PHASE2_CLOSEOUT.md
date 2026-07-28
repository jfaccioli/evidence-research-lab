# Phase 2 closeout — BTC long-only public-rule mandate

**Date:** 2026-07-28  
**Authority:** Human + standing scientific policy  
**Repo:** https://github.com/jfaccioli/evidence-research-lab (private)

---

## 1. What we set out to do

Build a **fail-closed** research lab that only promotes strategies after frozen gates, then paper → shadow → **tiny live** (no leverage).  
Goal is **reliable process** that *can* support autotrading when evidence exists — not “always be trading.”

---

## 2. What we concluded (this mandate)

Under **frozen gates**, **pre-registered programmes**, and **BTC long-only** rules on **daily / selective 4h** with lab costs:

| Result | Detail |
|--------|--------|
| Confirmatory candidates | **0** |
| Exploratory survivors that earned promotion | **None** (val teases died on confirmatory when tried) |
| Daily technical clone spam | **Paused** — low information gain |
| Funding / OI true PIT (v1 locks) | Programme-level nulls / confirmatory kill |
| Lab ops | **Mature** (`doctor`, `run-programme`, paper/shadow, kill switch) |

**Scientific reading:** This *slice* of the strategy space is hard. That is a high-quality null for the mandate, not a failure of the tool.

**We are not “ready for autotrading capital.”** The agent will say when we are **close** (see §6). Until then: no Phase 5, no gate softening.

---

## 3. Why other bots can “work” while we have zero candidates

Machines can outperform humans **in some games** (speed, discipline, bandwidth). That does **not** mean:

- every public technical bot is validated the way we validate, or  
- daily long-only filters under our costs/gates must work.

Other systems often use **different edge classes**, **higher risk**, **weaker validation**, or **survivorship** in public stories. Our bar is intentionally high so small Australian retail capital is not burned on fiction.

**Reliable autotrading remains a valid long-term goal** — via new evidence programmes, not shortcuts.

---

## 4. Phase 5 (tiny live) — what it is and when it helps

| Phase 5 is | Phase 5 is not |
|------------|----------------|
| Tiny real money (e.g. AUD 10–50), **spot only**, **no leverage** | The place you *discover* alpha |
| System test: fills, fees, kill switch, ops | Proof that backtests were right (that’s confirmatory + paper + shadow) |
| Only after **≥2–3 independent confirmatory survivors** (different mechanisms) + paper + shadow | Available with 0 candidates |

**How it helps us:** if/when science clears the bar, Phase 5 proves the *machine path* under real friction with limited downside.  
**How it hurts if early:** real losses + false confidence.

---

## 5. Roadmap — next research classes (no queue jump)

Order is **scientific**, not “coolest first.” All require **PIT history**, pre-registration, frozen gates.

| Priority | Programme class | Status | Notes |
|----------|-----------------|--------|--------|
| 0 | **Ops / lab reliability** | Ongoing | Default work when not designing a new class |
| 1 | **True exchange structure** (already touched) | v1 closed | Funding/OI done for locked hyps; reopen only with new design |
| 2 | **Flow / positioning (whales, large accounts)** | **Designed deferred** | See `docs/PROGRAMME_FLOW_WHALE_V1_DEFERRED.md` |
| 3 | **X / social attention (versioned PIT archive)** | **Deferred** | See ladder + deferred design sketch |
| 4 | **Polymarket / event odds (PIT)** | **Deferred** | After or alongside social only with reconstructible history |
| 5 | Microstructure / HFT-like | Out of current capital mandate | Different costs; optional later |

**X and Polymarket are remembered and scheduled** — they are **not** forgotten. They are **not** next-week live signals without PIT.

---

## 6. When you will hear “close to small-money autotrading”

Agent will flag **approaching readiness** only when **all** hold:

1. ≥ **2** independent **confirmatory** survivors (different mechanisms), under **unchanged** gates  
2. Each stable on paper path (fees, path, no hidden bug) for a pre-agreed window  
3. Shadow (live feed, no orders) reconciled  
4. **No leverage**, spot-only, risk envelope + kill switch tested  
5. Human explicit open for Phase 5 + keys  

**Today: not close.**

---

## 7. Leverage policy

**Lab policy: leverage = 0 / max 1.0 notional; no perps as the trading vehicle for Phase 5 personal capital.**

Reasons: risk of ruin; complexity; and Australian retail access to leveraged crypto products is **heavily restricted / high-risk** under ASIC settings — treat leverage as **out of mandate**, not a growth hack.  
*(Not legal advice; policy choice for this project.)*

Code already rejects `leverage != 1` in phase universe checks and risk envelope.

---

## 8. Success of this closeout

- Uncertainty reduced on public low-frequency long-only filters.  
- Tool ready for **better** questions (flow, event odds, social PIT).  
- Autotrading remains contingent on evidence — as originally intended when done properly.
