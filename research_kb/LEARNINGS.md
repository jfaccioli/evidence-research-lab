# Research knowledge base — learnings log

Updated after batches. Optimises *knowledge*, not win count.

---

## 2026-07-20 06:47 UTC

- Registry hypotheses: **115** (runs=232)
- Unique rule fingerprints: **71**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: asymmetric_capture, capacity_tiny_friction, atr_risk_trail, crowding_proxy

### Repeating failure modes

- **other** (n=288): See event reasons in registry.
- **low_sample** (n=189): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `asymmetric_capture`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `atr_risk_trail`: 4 ← underrepresented
- `crowding_proxy`: 5 ← underrepresented
- `slow_fast_disagreement`: 9
- `calendar_seasonality`: 10
- `liquidity_panic_rebound`: 11
- `vol_regime_shift`: 12
- `breakout_attention`: 13
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 21
- `vol_risk_premium`: 35
- `tsmom_underreaction`: 36
- `herding_trend`: 87

### Family recommendations

- `family_trend` [pivot] n=20 — All failed — try different mechanism, not nearby params.
- `family_momentum` [pivot] n=16 — All failed — try different mechanism, not nearby params.
- `family_composite` [pivot] n=13 — All failed — try different mechanism, not nearby params.
- `family_vol_filter` [pivot] n=12 — All failed — try different mechanism, not nearby params.
- `family_mean_reversion` [pivot] n=12 — All failed — try different mechanism, not nearby params.
- `family_calendar` [pivot] n=10 — All failed — try different mechanism, not nearby params.
- `family_volume` [pivot] n=10 — All failed — try different mechanism, not nearby params.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-20 07:31 UTC

- Registry hypotheses: **117** (runs=234)
- Unique rule fingerprints: **72**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: capacity_tiny_friction, asymmetric_capture, atr_risk_trail, crowding_proxy

### Repeating failure modes

- **low_sample** (n=191): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `capacity_tiny_friction`: 0 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 4 ← underrepresented
- `crowding_proxy`: 5 ← underrepresented
- `calendar_seasonality`: 10
- `slow_fast_disagreement`: 10
- `liquidity_panic_rebound`: 11
- `breakout_attention`: 13
- `vol_regime_shift`: 13
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 21
- `tsmom_underreaction`: 36
- `vol_risk_premium`: 36
- `herding_trend`: 89

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=1 passed_val=0 failed=0 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-20 07:41 UTC

- Registry hypotheses: **120** (runs=237)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: capacity_tiny_friction, liquidity_panic_rebound, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=194): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 34
- `herding_trend`: 60

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=1 passed_val=0 failed=1 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 06:55 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=10 passed_val=0 failed=10 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Funding PIT v1 gate autopsy (temp registry; not live)

**Programme:** `docs/PROGRAMME_FUNDING_PIT_V1.md`  
**Autopsy:** `examples/batch/funding/GATE_AUTOPSY_V1.md`  
**Batch:** 10/10 pre-reg, **0 `passed_val`**, true Binance funding PIT + daily OHLCV.

### What we learned

- High-quality **programme-level null** for locked daily long-only funding filters under frozen gates.
- Dominant killer: **bootstrap Sharpe CI lo &lt; 0** (8/10), not join errors.
- **min_trades** hits 6/10; two near-misses (`high_flat`, `trend_and_not_high`) fail *only* on trade count / reality few-trades despite positive excess and CI lo — power hint, **not** nomination.
- Mean-revert “long after negative funding” cluster is multi-gate dead (Sharpe, WF, fees, 2× cost).
- True funding is now in the evidence base for this operationalisation; OHLCV `funding_proxy` was never a substitute.

### Process constraints

- **Do not** mine more daily funding thresholds on the same data without a new programme version + multiplicity accounting.
- Optional next: pre-reg **4h power** study for level filters only; orthogonal **true OI** programme.
- No gate softening; no confirmatory; no live/paper/shadow.

### Mechanism update

- `funding_crowding`: stance remains **pivot**; daily pre-reg set treated as **exhausted_null**; confidence ↑ (mechanism status clearer, not expected alpha).


---

## 2026-07-27 — OI PIT v1 exploratory + confirmatory kill (temp registry)

**Programme:** `docs/PROGRAMME_OI_PIT_V1.md`  
**Autopsy:** `examples/batch/oi/GATE_AUTOPSY_V1.md`  
**OI series:** Bybit linear `bybit_oi_BTCUSDT_oi_b38c4e688cf0` (Binance public OI hist too shallow).  
**Batch:** 10/10 pre-reg exploratory → **1 `passed_val`**, **9 `failed_val`**; survivor **`failed_test`** on confirmatory.

### What we learned

- True OI is now in the evidence base (Bybit linear, disclosed cross-venue vs Binance spot OHLCV).
- **Val tease is not an edge:** `hyp_oi_chg_pct_high_flat` passed exploratory (n=30, Sh≈1.38) then confirmatory test Sh≈−0.10 — classic overfit / regime-specific pattern (regime concentration warn 0.97).
- Expanding-median raw **`oi_high` is a poor filter** under secular OI growth → three hyps with **0 val trades**.
- Bootstrap CI still dominant killer among non-sparse failures.
- No confirmatory candidate; do **not** mine OI thresholds on same data.

### Mechanism update

- `oi_leverage_stock`: **pivot**; daily pre-reg set closed without candidate; confidence ↑ on *status*, not alpha.


---

## 2026-07-27 10:08 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=10 passed_val=1 failed=9 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 10:14 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=6 passed_val=0 failed=6 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Funding 4h power study null (temp registry)

**Programme:** `docs/PROGRAMME_FUNDING_4H_POWER_V1.md`  
**Batch:** 6/6 pre-reg, **0 passed_val**, all n_trades ≥ 63.

### What we learned

- Daily funding near-misses (`min_trades`) were **not** latent edges waiting for power.
- 4h level/change/z funding filters fail WF/bootstrap/cost under frozen gates with ample trades.
- Funding long-only filter line (daily + 4h locks) is **exhausted** for this pre-reg family — stop mining.


## 2026-07-27 10:23 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=4 errors=1

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 10:24 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Capacity tiny-friction v1 null

Elevated costs, frozen gates, 0/5 passed_val. Pipeline fix: SMA sensitivity no longer corrupts `sma_N_above_M` tokens.


## 2026-07-27 10:29 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Asymmetric v2 null + production scaffold

- Asymmetric capture v2: 0/5 exploratory under frozen gates.
- Paper/Shadow brokers scaffolded; LIVE dual-flag + no adapter (fail-closed).
- Destination remains tiny live when ladder earned — not skipped.


## 2026-07-27 10:30 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Liquidity panic v1 null

0/5 exploratory. Sparse rebounds fail trade count; volume dry-up fails WF/bootstrap.


## 2026-07-27 10:34 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 10:34 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 10:34 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=1 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — ATR / slow-fast / vol-regime programmes + paper CLI

- atr_trail: 0/5 exploratory
- slow_fast: 0/5 exploratory
- vol_regime: 1/5 passed_val (`hyp_vr_exit_volspike`) → confirmatory **failed_test**
- `crl paper` historical paper session wired (no exchange)
- Still **zero candidates** for paper capital clock


## 2026-07-27 10:35 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Calendar v1 null

0/5 exploratory under frozen gates.


## 2026-07-27 10:38 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 10:38 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Breakout + volume nulls; paper replay + shadow walk

- breakout_attention v1: 0/5 exploratory
- volume_confirmation v1: 0/5 exploratory  
- `crl paper --hyp-dir` replay and `crl shadow` historical walk wired
- Paper full-sample equity is **not** promotion evidence
- Meta synthesis: docs/META_NULL_SYNTHESIS_2026-07-27.md


## 2026-07-27 10:39 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Breakout 4h power null

0/4 with ample trades on most hyps — not pure power. WF + bootstrap dominate.

## 2026-07-27 10:46 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Hold 4h null + scientific outlook

- 4h low-turnover holds: 0/4 exploratory (WF + bootstrap).
- Outlook: good autotrading from daily/4h public long-only rules under frozen gates looks **unlikely so far**; lab value is honest rejection.
- Paper sessions now report max_drawdown; still not promotion evidence.


## 2026-07-27 10:51 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Reliability pass + fade null

- `crl doctor` health surface; programme batch defaults avoid catalog clobber
- Stretch fade v1: 0/4 exploratory
- Mandate doc: docs/MANDATE_CURRENT_SCOPE.md (strong tool ≠ forced alpha)


## 2026-07-27 10:57 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Tooling: programmes inventory, temp-registry, risk envelope

- `crl programmes`, `--temp-registry`, risk envelope for future LIVE
- risk_off v1: 0/4 exploratory

## 2026-07-27 11:00 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Kill switch, status CLI, risk in paper, herding null

- Kill switch file/env; paper respects kill + optional mandate limits
- `crl status`; APPROVED strategies empty by design
- herding v1: 0/4 exploratory

## 2026-07-27 11:01 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-27 — Paper report MD + mr_trend null

- paper replay writes replay_summary.md
- ops KILL_SWITCH default off tracked under data/ops/
- mr_trend v1: 0/4 exploratory

## 2026-07-28 00:17 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 00:17 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=1 passed_val=0 failed=1 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — run-programme + 4h dataset inference

- `crl run-programme`: doctor + temp registry + EXPLORATORY_NOTE refresh
- `run_batch` infers 1d/4h dataset from hyp timeframe
- Shadow respects kill switch

## 2026-07-28 00:25 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 00:25 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 00:25 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 00:26 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — autopsy CLI + trend_quality/volume_4h nulls

- `crl autopsy` + auto autopsy on run-programme
- trend_quality: 0/4; volume_4h: 0/4 (fee_fragile / WF on higher frequency)
- Doctor soft-warns missing notes so new programmes can run

## 2026-07-28 00:29 UTC

- Registry hypotheses: **123** (runs=240)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture, atr_risk_trail

### Repeating failure modes

- **low_sample** (n=197): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 63

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=4 passed_val=0 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — README ops refresh + participation null

- README matches current CLI surface
- status --write-md → docs/LAB_STATUS.md
- participation v1: 0/4 (bootstrap; one near-miss CI lo ≈ 0)

## 2026-07-28 — Phase 2 closeout + deferred flow/X/Polymarket + no leverage

- Closeout: public-rule daily/4h mandate has 0 confirmatory candidates; lab remains product
- Deferred designs: flow/whale, X, Polymarket (PIT only)
- Leverage forbidden as trading vehicle; AU high-risk context noted (not legal advice)
- Agent will flag when close to tiny live (not now)

## 2026-07-28 04:54 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=8 passed_val=6 failed=2 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 04:58 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — Autonomy sprint: flow + Coinbase premium

### Flow (cmd_btc_exchange_netflow_v1)
- Free series + publish_lag=1; attribution crypto-market-data CC BY 4.0.
- Exploratory 6/8 passed_val (strong val Sharpes ~1.2–1.5).
- Confirmatory **0/6**: all failed_test (neg test Sharpe, fee_fragile, bootstrap CI).
- **Lesson:** same val-tease pattern as OI/vol-regime; do not promote on val alone.

### Coinbase premium (cmd_btc_coinbase_premium_index_v1)
- Distinct mechanism (US premium); 5 locked hyps; same lag policy.
- Exploratory **0/5** passed_val (bootstrap / trades / other gates).
- **Lesson:** free premium series does not clear exploratory under frozen gates.

### Product
- Still 0 APPROVED; autotrading not closer via promotion.
- Shortest path remains: new PIT info class (Polymarket archive) or accept lab-only.
- CryptoQuant **not required** for first flow test (done via free mirror); optional for vendor-grade PIT upgrade only.

## 2026-07-28 05:26 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 05:26 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — Polymarket v1 (public CLOB)

- Locked series: YES price for "BTC reach $150k by EOY 2025" (not max-variance pick).
- n≈368 daily points; windowed BTC dataset for fair val (full history put PM only in late sample).
- Exploratory **0/5** passed_val (mostly n_trades ≪ 30 under sticky long-only rules + short series).
- **Lesson:** Free Polymarket history exists without keys, but **year-end binary odds + sticky long-only + min_trades=30** is a weak experimental design. Do not weaken gates; redesign only with new programme version (e.g. different event class, non-sticky rules, longer multi-market panel) if revisited.
- Still **0** confirmatory candidates overall.

## 2026-07-28 05:44 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 05:45 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=1 failed=4 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 05:45 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — Research Director free-series wave (Q4–Q6)

Standing Research Director Directive adopted. Ran without waiting:

| Programme | Expl | Conf |
|-----------|------|------|
| Stablecoin exchange netflow | 0/5 | — |
| Long liquidations | 1/5 | 0/1 failed_test |
| MVRV | 0/5 | — |

Combined with Q1/Q1b/Q2: **still zero confirmatory candidates**.

**Director decision:** Stop grinding free daily CMD-style filters for long-only BTC under frozen gates. Expected value of the next similar series is low. Prefer (a) genuinely new data class with archive, (b) human vendor-grade series, or (c) honest lab-only pause.

Gates unchanged. No APPROVED. No tiny-live path opened.

## 2026-07-28 07:19 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — Strategic Research Review + scientific pause

- Lab-level critique completed (`docs/STRATEGIC_RESEARCH_REVIEW_2026-07-28.md`).
- Mandate kept (spot long-only, frozen gates); scope not widened to leverage/HFT.
- Highest free Alpha item executed: **PM multi-market panel** (5 pre-reg legs) → explor **0/5**.
- Free macro/ETF acquisition blocked without keys.
- **Human Action Packet** issued; autonomous science paused until new information (prefer vendor netflow export or FRED/ETF unlock).
- Still **0** confirmatory candidates. Gates unchanged.

## 2026-07-28 07:42 UTC

- Registry hypotheses: **124** (runs=241)
- Unique rule fingerprints: **73**

### What we learned

- Zero confirmatory candidates in registry.
- Underrepresented mechanisms: oi_leverage_stock, flow_whale, capacity_tiny_friction, liquidity_panic_rebound, funding_crowding, asymmetric_capture

### Repeating failure modes

- **low_sample** (n=198): Rules too sparse on daily bars — need more trades or different horizon.
- **weak_sharpe** (n=36): No risk-adjusted edge after costs on evaluated splits.
- **reality** (n=2): Statistically cute but economically/executionally weak.

### Mechanism coverage

- `oi_leverage_stock`: 0 ← underrepresented
- `flow_whale`: 0 ← underrepresented
- `capacity_tiny_friction`: 0 ← underrepresented
- `liquidity_panic_rebound`: 1 ← underrepresented
- `funding_crowding`: 1 ← underrepresented
- `asymmetric_capture`: 1 ← underrepresented
- `atr_risk_trail`: 2 ← underrepresented
- `crowding_proxy`: 3
- `vol_regime_shift`: 4
- `slow_fast_disagreement`: 4
- `breakout_attention`: 10
- `calendar_seasonality`: 10
- `mean_reversion_cross_section_proxy`: 14
- `volume_confirmation`: 18
- `tsmom_underreaction`: 31
- `vol_risk_premium`: 37
- `herding_trend`: 64

### Family recommendations

- `family_trend` [retire] n=20 — Large family (20) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_momentum` [retire] n=16 — Large family (16) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_composite` [retire] n=13 — Large family (13) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_vol_filter` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_mean_reversion` [retire] n=12 — Large family (12) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_calendar` [retire] n=10 — Large family (10) nearly all failed, dominant tag=weak_sharpe; diminishing returns.
- `family_volume` [retire] n=10 — Large family (10) nearly all failed, dominant tag=low_sample; diminishing returns.
- `family_sentiment_proxy` [pivot] n=4 — All failed — try different mechanism, not nearby params.
- `family_onchain_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `family_funding_proxy` [pivot] n=3 — All failed — try different mechanism, not nearby params.
- `hyp_e2e_mock_1784522180` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `family_trend_vol_filter` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784522240` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784523788` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.
- `hyp_e2e_mock_1784524120` [continue] n=1 — Thin evidence — one more *distinct* test may still inform.

### Retire (exhausted) families

`family_trend`, `family_momentum`, `family_composite`, `family_vol_filter`, `family_mean_reversion`, `family_calendar`, `family_volume`

### Latest batch snapshot

- run=5 passed_val=0 failed=5 errors=0

### Planner stance

- Prefer underrepresented mechanisms with high information gain.
- Do not clone exhausted families.
- Null results that cleanly retire a mechanism are valuable.


---

## 2026-07-28 — MACRO_REGIME_V1 (FRED)

### Series locked
- **DTWEXBGS** (broad USD index): risk-off when USD strong.
- **DGS2** (2Y Treasury): tightening pulse / policy path.
- Excluded DFF/DGS10/VIX in v1 (multiplicity / scope).

### PIT
- `publish_lag_days=1` on FRED date → no same-day use.
- Snapshot download (not ALFRED vintages).

### Results
- Exploratory **0/5** under frozen gates (mostly n_trades < 30 or negative Sharpe / fee_fragile).
- Confirmatory not earned. **0 candidates.**

### Implication
- Free macro regime operationalisation does **not** clear bar.
- EIR next tier (ETF free source or vendor export) may be reconsidered with fresh investment review.

## 2026-07-28 — Search space review → Roadmap V2

- V1 grammar (unconditional daily long/flat on public levels) exhausted across technicals, funding/OI, free on-chain, PM, FRED macro — 0 confirmatory survivors.
- **Not** interpreted as lab failure; interpreted as incomplete **hypothesis class** space.
- New directions ranked: vol forecast/risk policy, cross-asset transfer, conditional relationships, risk-as-edge; defer L2/adaptive ML soup; reject more CMD clones.
- **RESEARCH_ROADMAP_V2** adopted; next implementable free programme class: **V2-A vol forecast → position policy** (BTC OHLCV already in lab).

## 2026-07-28 — Evidence aggregation architecture study

- User observation: real decisions combine many weak evidences; lab still atomistic (signal→trade).
- Study: public quant practice favours forecast combination, calibration, separation of forecast/risk/decision — not single indicators.
- **Reject** free-text multi-agent LLM committees as promotion path.
- **Adopt target architecture:** Evidence Channel Architecture (ECA) — numeric PIT evidence streams → frozen aggregator → decision policy under existing gates.
- V2-A not cancelled: **re-scoped** as ECA-1 vol/risk channel; **not implemented** until ECA-0 protocol; do not ship V2-A as another standalone signal programme.
