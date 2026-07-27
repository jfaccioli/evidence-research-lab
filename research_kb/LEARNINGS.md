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

