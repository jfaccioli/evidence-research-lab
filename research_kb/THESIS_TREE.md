# Research Thesis Tree

**Updated:** `2026-07-30T02:19:28.376416+00:00`  
**Summary:** [NON-AUTHORITATIVE] 17 mechanisms tracked; 6 closed/retired/null; 11 still open; registry n=124. Success = uncertainty reduction, not alpha discovery.

Epistemic map of *economic mechanisms*. Confidence = certainty about the **scientific status** of the claim, not expected returns.

Nomination ≠ promotion: confirmatory still requires **existing validation gates**.

## Global unknowns

- No confirmatory *candidates* yet — uncertainty remains high on all mechanisms.
- Daily BTC long-only space may be saturated with public technical rules.
- True funding/OI/on-chain PIT series not yet in evidence base.
- Whether *any* low-frequency BTC spot edge survives costs + multiple testing is open.

## Mechanisms

### `tsmom_underreaction` — Time-series momentum / underreaction

- **Stance:** `active` (confidence 0.40)
- **Recommendation:** `pivot`
- **Claim:** Gradual diffusion of information; intermediate returns continue.
- **Evidence mass:** n_tests=31, passed_val=0, failed_test=1, candidate=0

**Supporting**

- Exploratory gates can pass with 30 trades and decent val Sharpe.
- No strong supporting evidence on val.

**Refuting**

- Confirmatory kill: test Sharpe negative, fee-fragile, multiple-testing, overfit gap. Val-only momentum teases are not edges.
- Failed exploratory gates: n_trades 22 < min_trades 30; bootstrap sharpe CI lo -0.469 < 0.0 Val excess vs B&H = -0.733.
- Failures dominate (failed≈30, n=31); no exploratory survival yet.
- hyp_mom_30_pos: confirmatory failed (negative test Sharpe, MT, fees).

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- Whether slower/faster pure TSMOM with different horizons is exhausted.
- Whether disagreement entries need different horizons or vol filters.
- May still be open under a different operationalisation.

### `crowding_proxy` — Crowding / leverage stress proxy

- **Stance:** `active` (confidence 0.40)
- **Recommendation:** `pivot`
- **Claim:** High-vol or crowded risk-on states precede unwind (proxy only).
- **Evidence mass:** n_tests=4, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Failures dominate (failed≈4, n=4); no exploratory survival yet.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- May still be open under a different operationalisation.

### `slow_fast_disagreement` — Slow vs fast signal disagreement

- **Stance:** `active` (confidence 0.40)
- **Recommendation:** `pivot`
- **Claim:** When short-horizon mom disagrees with long trend, edge may be in resolution.
- **Evidence mass:** n_tests=4, passed_val=0, failed_test=0, candidate=0

**Supporting**

- No strong supporting evidence on val.

**Refuting**

- Failed exploratory gates: n_trades 22 < min_trades 30; bootstrap sharpe CI lo -0.469 < 0.0 Val excess vs B&H = -0.733.
- Failures dominate (failed≈4, n=4); no exploratory survival yet.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- Whether disagreement entries need different horizons or vol filters.
- May still be open under a different operationalisation.

### `vol_regime_shift` — Volatility regime-shift risk

- **Stance:** `active` (confidence 0.40)
- **Recommendation:** `pivot`
- **Claim:** Rising vol marks stress transitions; reduce exposure.
- **Evidence mass:** n_tests=4, passed_val=0, failed_test=0, candidate=0

**Supporting**

- Process: underrepresented mechanism tested; lower val DD than B&H observed.

**Refuting**

- Insurance claim unsupported for this formulation: val excess vs B&H ≈ -0.95; failed min_trades and bootstrap CI. Shallower DD without economic value is not an edge.
- Failures dominate (failed≈4, n=4); no exploratory survival yet.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- Whether a non-SMA asymmetric design could cut left tail without destroying excess.
- May still be open under a different operationalisation.

### `liquidity_panic_rebound` — Forced selling / panic rebound

- **Stance:** `active` (confidence 0.40)
- **Recommendation:** `pivot`
- **Claim:** Sharp selloffs reverse when temporary liquidity demand fades.
- **Evidence mass:** n_tests=3, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Failures dominate (failed≈3, n=3); no exploratory survival yet.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- May still be open under a different operationalisation.

### `atr_risk_trail` — Volatility-scaled risk trailing

- **Stance:** `active` (confidence 0.35)
- **Recommendation:** `pivot`
- **Claim:** Position held only when price respects ATR-based risk budget.
- **Evidence mass:** n_tests=2, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Early failure(s) — formulation-specific; mechanism not fully closed.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- Underrepresented in catalog — remaining uncertainty high.

### `funding_crowding` — Perpetual funding / leverage crowding (true series)

- **Stance:** `active` (confidence 0.35)
- **Recommendation:** `pivot`
- **Claim:** Funding rate as cost of leverage and crowded positioning; PIT exchange series only.
- **Evidence mass:** n_tests=2, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Early failure(s) — formulation-specific; mechanism not fully closed.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- Underrepresented in catalog — remaining uncertainty high.

### `asymmetric_capture` — Asymmetric upside/downside capture vs B&H

- **Stance:** `active` (confidence 0.45)
- **Recommendation:** `pivot`
- **Claim:** Rule aims to cut left-tail BTC path while keeping right-tail (insurance-like).
- **Evidence mass:** n_tests=1, passed_val=0, failed_test=0, candidate=0

**Supporting**

- Process: underrepresented mechanism tested; lower val DD than B&H observed.

**Refuting**

- Insurance claim unsupported for this formulation: val excess vs B&H ≈ -0.95; failed min_trades and bootstrap CI. Shallower DD without economic value is not an edge.
- Early failure(s) — formulation-specific; mechanism not fully closed.
- plan_asymmetric_capture_vol_gate: val excess vs B&H strongly negative despite lower DD — insurance claim not supported for that formulation.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- Whether a non-SMA asymmetric design could cut left tail without destroying excess.
- Underrepresented in catalog — remaining uncertainty high.

### `capacity_tiny_friction` — Tiny-capital friction realism

- **Stance:** `untested` (confidence 0.10)
- **Recommendation:** `observe`
- **Claim:** Edges that only work with zero friction are invalid for 10–50 AUD.
- **Evidence mass:** n_tests=0, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- _(none logged)_

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- No direct tests yet — high IG if economically distinct.
- Underrepresented in catalog — remaining uncertainty high.

### `flow_whale` — Exchange flow / large-player positioning (true series)

- **Stance:** `untested` (confidence 0.10)
- **Recommendation:** `observe`
- **Claim:** PIT net exchange flow or large transfers; not unversioned whale alerts.
- **Evidence mass:** n_tests=0, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- _(none logged)_

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- No direct tests yet — high IG if economically distinct.
- Underrepresented in catalog — remaining uncertainty high.

### `oi_leverage_stock` — Open interest / leverage stock (true series)

- **Stance:** `untested` (confidence 0.10)
- **Recommendation:** `observe`
- **Claim:** Exchange-native OI as stock of open leverage; PIT snapshots only — not funding.
- **Evidence mass:** n_tests=0, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- _(none logged)_

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- No direct tests yet — high IG if economically distinct.
- Underrepresented in catalog — remaining uncertainty high.

### `herding_trend` — Herding / risk-on trend following

- **Stance:** `exhausted_null` (confidence 0.75)
- **Recommendation:** `retire`
- **Claim:** Capital chases established price trends; SMA/EMA as flow proxies.
- **Evidence mass:** n_tests=64, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Large null body (n≈64) with no exploratory survival.
- Heavy testing of SMA/EMA trend class; no confirmatory path so far.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.

### `vol_risk_premium` — Volatility risk preference / quiet markets

- **Stance:** `exhausted_null` (confidence 0.70)
- **Recommendation:** `retire`
- **Claim:** Agents prefer risk when realized vol is low.
- **Evidence mass:** n_tests=38, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Large null body (n≈38) with no exploratory survival.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.

### `volume_confirmation` — Volume confirmation of price moves

- **Stance:** `exhausted_null` (confidence 0.70)
- **Recommendation:** `retire`
- **Claim:** Moves without volume are less reliable; thrust needs participation.
- **Evidence mass:** n_tests=18, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Large null body (n≈18) with no exploratory survival.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.

### `mean_reversion_cross_section_proxy` — Relative value / stretch vs own history only

- **Stance:** `exhausted_null` (confidence 0.70)
- **Recommendation:** `retire`
- **Claim:** Extreme z-score stretches mean-revert when not in structural bear.
- **Evidence mass:** n_tests=14, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- Large null body (n≈14) with no exploratory survival.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.

### `breakout_attention` — Breakout + attention / participation

- **Stance:** `refuted` (confidence 0.50)
- **Recommendation:** `pivot`
- **Claim:** New highs with volume reflect information incorporation.
- **Evidence mass:** n_tests=11, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- All 11 tests failed exploratory/gates under current design class.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- A structurally different operationalisation might still be open.

### `calendar_seasonality` — Calendar / seasonality microstructure

- **Stance:** `refuted` (confidence 0.50)
- **Recommendation:** `pivot`
- **Claim:** Day-of-week or month-end effects from institutional calendars.
- **Evidence mass:** n_tests=10, passed_val=0, failed_test=0, candidate=0

**Supporting**

- _(none logged)_

**Refuting**

- All 10 tests failed exploratory/gates under current design class.

**Remaining unknowns**

- OOS confirmatory not earned or not run.
- Multiple-testing burden grows with family size.
- A structurally different operationalisation might still be open.

---

*Chief Research Scientist mode: maximise knowledge per budget unit.*
