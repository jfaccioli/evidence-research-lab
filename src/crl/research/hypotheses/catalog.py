"""Pre-registered Phase-1 hypothesis library (~50 falsifiable rules).

All ideas are OHLCV-only or clearly labeled *proxies* (not live X, not
true on-chain, not perpetual funding unless a PIT series is joined later).
Generate YAML files under examples/batch/ for batch exploratory runs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# (id_suffix, taxonomy, entry, exit, rationale, expected)
# family_id defaults to taxonomy for meta-analysis
CATALOG: list[dict[str, Any]] = [
    # ----- TREND (8) -----
    {
        "slug": "sma200_long",
        "taxonomy": "trend",
        "entry": "close > sma_200",
        "exit": "close < sma_200",
        "rationale": "Classic price above 200d SMA trend filter.",
        "expected": "Captures major bulls; large DD; may not beat B&H after costs.",
    },
    {
        "slug": "sma50_long",
        "taxonomy": "trend",
        "entry": "close > sma_50",
        "exit": "close < sma_50",
        "rationale": "Shorter SMA trend filter.",
        "expected": "More trades, more costs; fragile.",
    },
    {
        "slug": "sma50_200_cross",
        "taxonomy": "trend",
        "entry": "sma_50 > sma_200",
        "exit": "sma_50 < sma_200",
        "rationale": "Golden/death cross style dual SMA.",
        "expected": "Few trades; well-known; crowding risk.",
    },
    {
        "slug": "sma20_50_cross",
        "taxonomy": "trend",
        "entry": "sma_20 > sma_50",
        "exit": "sma_20 < sma_50",
        "rationale": "Faster dual SMA cross.",
        "expected": "Higher turnover; cost-sensitive.",
    },
    {
        "slug": "ema200_long",
        "taxonomy": "trend",
        "entry": "close > ema_200",
        "exit": "close < ema_200",
        "rationale": "EMA(200) trend filter.",
        "expected": "Similar to SMA200 with slightly faster response.",
    },
    {
        "slug": "price_above_sma100",
        "taxonomy": "trend",
        "entry": "close > sma_100",
        "exit": "close < sma_100",
        "rationale": "Intermediate 100d trend.",
        "expected": "Between SMA50 and SMA200 behavior.",
    },
    {
        "slug": "dual_confirm_20_200",
        "taxonomy": "trend",
        "entry": "close > sma_20 and close > sma_200",
        "exit": "close < sma_200",
        "rationale": "Require short and long trend alignment to enter.",
        "expected": "Fewer entries; may miss early trend.",
    },
    {
        "slug": "sma_stack_bull",
        "taxonomy": "trend",
        "entry": "sma_20 > sma_50 and sma_50 > sma_200",
        "exit": "sma_50 < sma_200",
        "rationale": "Full SMA stack bullish.",
        "expected": "Late entries; fewer trades.",
    },
    # ----- VOL FILTER (6) -----
    {
        "slug": "long_low_vol_only",
        "taxonomy": "vol_filter",
        "entry": "close > sma_200 and rvol_below_median > 0.5",
        "exit": "close < sma_200",
        "rationale": "Trend only when realized vol below expanding median.",
        "expected": "May cut DD; sample size risk on val.",
    },
    {
        "slug": "long_high_vol_breakout",
        "taxonomy": "vol_filter",
        "entry": "close > sma_50 and rvol_above_median > 0.5",
        "exit": "close < sma_50",
        "rationale": "Hold trend only in elevated vol regimes.",
        "expected": "May increase noise and costs.",
    },
    {
        "slug": "flat_when_vol_spikes",
        "taxonomy": "vol_filter",
        "entry": "close > sma_100 and rvol_below_median > 0.5",
        "exit": "rvol_above_median > 0.5 or close < sma_100",
        "rationale": "Exit when vol expands above expanding median.",
        "expected": "Regime timing; few clean trades.",
    },
    {
        "slug": "atr_compression_long",
        "taxonomy": "vol_filter",
        "entry": "close > sma_50 and atr_pct < 0.03",
        "exit": "close < sma_50 or atr_pct > 0.06",
        "rationale": "Enter calm ATR% regimes with intermediate trend.",
        "expected": "Thresholds arbitrary; fragility likely.",
    },
    {
        "slug": "vol_decline_trend",
        "taxonomy": "vol_filter",
        "entry": "close > sma_200 and rvol_20_chg < 0",
        "exit": "close < sma_200",
        "rationale": "Trend when short-term vol is declining.",
        "expected": "Weak economic story; likely noise.",
    },
    {
        "slug": "always_in_low_vol",
        "taxonomy": "vol_filter",
        "entry": "rvol_below_median > 0.5",
        "exit": "rvol_above_median > 0.5",
        "rationale": "Long only in low-vol half of history (causal median).",
        "expected": "Misses high-vol bulls; tests pure vol timing.",
    },
    # ----- MOMENTUM (7) -----
    {
        "slug": "mom_20_pos",
        "taxonomy": "momentum",
        "entry": "ret_20 > 0",
        "exit": "ret_20 < 0",
        "rationale": "20-bar return sign momentum.",
        "expected": "Classic TSMOM; costs and crypto regimes matter.",
    },
    {
        "slug": "mom_60_pos",
        "taxonomy": "momentum",
        "entry": "ret_60 > 0",
        "exit": "ret_60 < 0",
        "rationale": "60-bar return sign momentum.",
        "expected": "Slower momentum; fewer flips.",
    },
    {
        "slug": "mom_20_strong",
        "taxonomy": "momentum",
        "entry": "ret_20 > 0.05",
        "exit": "ret_20 < 0",
        "rationale": "Require +5% 20-bar thrust to enter.",
        "expected": "Late entries; may reduce false starts.",
    },
    {
        "slug": "mom_dual_20_60",
        "taxonomy": "momentum",
        "entry": "ret_20 > 0 and ret_60 > 0",
        "exit": "ret_20 < 0 or ret_60 < 0",
        "rationale": "Dual-horizon momentum alignment.",
        "expected": "Stricter; fewer trades.",
    },
    {
        "slug": "mom_10_fast",
        "taxonomy": "momentum",
        "entry": "ret_10 > 0",
        "exit": "ret_10 < 0",
        "rationale": "Fast 10-bar momentum.",
        "expected": "High turnover; fee stress fails often.",
    },
    {
        "slug": "mom_with_trend",
        "taxonomy": "momentum",
        "entry": "ret_20 > 0 and close > sma_200",
        "exit": "ret_20 < 0 or close < sma_200",
        "rationale": "Momentum only with long-term uptrend.",
        "expected": "Composite-ish; common quant stack.",
    },
    {
        "slug": "mom_skip_high_vol",
        "taxonomy": "momentum",
        "entry": "ret_20 > 0 and rvol_below_median > 0.5",
        "exit": "ret_20 < 0",
        "rationale": "Momentum entries filtered by low vol.",
        "expected": "May help or starve sample size.",
    },
    # ----- MEAN REVERSION (6) -----
    {
        "slug": "fade_price_z20",
        "taxonomy": "mean_reversion",
        "entry": "price_z_20 < -1.5 and close > sma_200",
        "exit": "price_z_20 > 0 or close < sma_200",
        "rationale": "Buy dips vs 20d z-score only in uptrend.",
        "expected": "Crypto trends hard; MR often fails.",
    },
    {
        "slug": "fade_dist_sma20",
        "taxonomy": "mean_reversion",
        "entry": "dist_sma_20 < -0.08",
        "exit": "dist_sma_20 > 0",
        "rationale": "Enter when >8% below SMA20.",
        "expected": "Catching falling knives in bears.",
    },
    {
        "slug": "fade_dist_sma50_trend",
        "taxonomy": "mean_reversion",
        "entry": "dist_sma_50 < -0.10 and close > sma_200",
        "exit": "dist_sma_50 > -0.02 or close < sma_200",
        "rationale": "Dip-buy vs SMA50 in bull regime.",
        "expected": "Works only if pullbacks mean-revert.",
    },
    {
        "slug": "rsi_like_z_revert",
        "taxonomy": "mean_reversion",
        "entry": "price_z_60 < -2",
        "exit": "price_z_60 > -0.5",
        "rationale": "Deep 60d underextension reversion.",
        "expected": "Rare signals; small N risk.",
    },
    {
        "slug": "short_stretch_exit_only_long",
        "taxonomy": "mean_reversion",
        "entry": "close > sma_200 and dist_sma_20 < -0.05",
        "exit": "dist_sma_20 > 0.02 or close < sma_200",
        "rationale": "Mild dip buy in uptrend.",
        "expected": "Mild edge or none after costs.",
    },
    {
        "slug": "fade_up_extension_avoid",
        "taxonomy": "mean_reversion",
        "entry": "close > sma_200 and price_z_20 < 1.5",
        "exit": "close < sma_200 or price_z_20 > 2.0",
        "rationale": "Stay long in trend but step aside on extreme upside z.",
        "expected": "Tests whether avoiding blow-off tops helps.",
    },
    # ----- VOLUME (5) -----
    {
        "slug": "vol_confirm_trend",
        "taxonomy": "volume",
        "entry": "close > sma_50 and vol_z_20 > 0.5",
        "exit": "close < sma_50",
        "rationale": "Trend entry requires elevated volume z-score.",
        "expected": "Participation filter; mixed evidence historically.",
    },
    {
        "slug": "vol_dryup_trend",
        "taxonomy": "volume",
        "entry": "close > sma_200 and vol_z_20 < 0",
        "exit": "close < sma_200",
        "rationale": "Trend with quiet volume.",
        "expected": "Unclear economic mechanism.",
    },
    {
        "slug": "vol_ratio_thrust",
        "taxonomy": "volume",
        "entry": "vol_ratio_20 > 1.5 and ret_5 > 0",
        "exit": "ret_5 < 0",
        "rationale": "Volume thrust + short positive return.",
        "expected": "Noisy; high turnover risk.",
    },
    {
        "slug": "high_vol_z_breakout",
        "taxonomy": "volume",
        "entry": "vol_z_20 > 1.0 and close > sma_20",
        "exit": "close < sma_20",
        "rationale": "Breakout-style volume spike + short trend.",
        "expected": "Many false breakouts.",
    },
    {
        "slug": "vol60_trend",
        "taxonomy": "volume",
        "entry": "close > sma_100 and vol_z_60 > 0",
        "exit": "close < sma_100",
        "rationale": "Longer volume z confirmation.",
        "expected": "Weaker filter; similar to bare trend.",
    },
    # ----- CALENDAR (6) -----
    {
        "slug": "avoid_weekend_hold_weekdays",
        "taxonomy": "calendar",
        "entry": "is_weekend < 0.5 and close > sma_200",
        "exit": "is_weekend > 0.5 or close < sma_200",
        "rationale": "Hold trend only on weekdays (UTC).",
        "expected": "Crypto 24/7; weekend effect may be myth.",
    },
    {
        "slug": "monday_entry_bias",
        "taxonomy": "calendar",
        "entry": "is_monday > 0.5 and close > sma_50",
        "exit": "close < sma_50",
        "rationale": "Only allow new exposure logic via Monday+trend (state machine).",
        "expected": "Odd timing; likely fails trade count or edge.",
    },
    {
        "slug": "friday_flat",
        "taxonomy": "calendar",
        "entry": "is_friday < 0.5 and close > sma_100",
        "exit": "is_friday > 0.5 or close < sma_100",
        "rationale": "Avoid holding over Friday close (UTC).",
        "expected": "Calendar folklore; expect reject.",
    },
    {
        "slug": "month_end_risk_off",
        "taxonomy": "calendar",
        "entry": "is_month_end < 0.5 and close > sma_200",
        "exit": "is_month_end > 0.5 or close < sma_200",
        "rationale": "Flat near month-end days.",
        "expected": "Weak prior; multiple-testing risk.",
    },
    {
        "slug": "month_start_long",
        "taxonomy": "calendar",
        "entry": "is_month_start > 0.5 and close > sma_50",
        "exit": "is_month_start < 0.5 or close < sma_50",
        "rationale": "Only long on first days of month + mild trend.",
        "expected": "Very few holding periods; low N.",
    },
    {
        "slug": "weekend_only_long",
        "taxonomy": "calendar",
        "entry": "is_weekend > 0.5",
        "exit": "is_weekend < 0.5",
        "rationale": "Long only on weekends (pure calendar).",
        "expected": "Should fail if no weekend premium.",
    },
    # ----- COMPOSITE (6) -----
    {
        "slug": "trend_vol_volume",
        "taxonomy": "composite",
        "entry": "close > sma_200 and rvol_below_median > 0.5 and vol_z_20 > 0",
        "exit": "close < sma_200",
        "rationale": "Trend + low vol + volume participation.",
        "expected": "Over-constrained; sample risk.",
    },
    {
        "slug": "mom_trend_vol",
        "taxonomy": "composite",
        "entry": "ret_20 > 0 and close > sma_200 and rvol_below_median > 0.5",
        "exit": "ret_20 < 0 or close < sma_200",
        "rationale": "Momentum + trend + vol filter stack.",
        "expected": "Popular quant kitchen sink; may overfit narrative.",
    },
    {
        "slug": "cross_vol_filter",
        "taxonomy": "composite",
        "entry": "sma_50 > sma_200 and rvol_below_median > 0.5",
        "exit": "sma_50 < sma_200",
        "rationale": "Golden cross state with low vol.",
        "expected": "Few trades.",
    },
    {
        "slug": "dip_buy_composite",
        "taxonomy": "composite",
        "entry": "close > sma_200 and dist_sma_20 < -0.06 and vol_z_20 > 0.5",
        "exit": "dist_sma_20 > 0 or close < sma_200",
        "rationale": "Dip + volume + long trend.",
        "expected": "MR+volume story; often fails in crashes.",
    },
    {
        "slug": "ema_stack_mom",
        "taxonomy": "composite",
        "entry": "close > ema_50 and ret_10 > 0 and rvol_below_median > 0.5",
        "exit": "close < ema_50 or ret_10 < 0",
        "rationale": "EMA trend + fast mom + vol.",
        "expected": "Complex; fragility likely.",
    },
    {
        "slug": "sma100_mom60",
        "taxonomy": "composite",
        "entry": "close > sma_100 and ret_60 > 0",
        "exit": "close < sma_100 or ret_60 < 0",
        "rationale": "Medium trend + medium momentum.",
        "expected": "Reasonable prior; still must clear gates.",
    },
    # ----- SENTIMENT PROXY (4) — volume/vol as attention, NOT X -----
    {
        "slug": "attention_vol_spike_trend",
        "taxonomy": "sentiment_proxy",
        "entry": "vol_z_20 > 1.5 and close > sma_50",
        "exit": "close < sma_50",
        "rationale": "PROXY for attention/sentiment via volume spike + trend (not social data).",
        "expected": "Proxy may not map to true sentiment; treat as volume test.",
    },
    {
        "slug": "attention_dry_bull",
        "taxonomy": "sentiment_proxy",
        "entry": "vol_z_20 < -0.5 and close > sma_200",
        "exit": "close < sma_200",
        "rationale": "PROXY: low attention (quiet volume) bull continuation.",
        "expected": "Narrative weak; likely reject.",
    },
    {
        "slug": "fear_vol_high_avoid",
        "taxonomy": "sentiment_proxy",
        "entry": "close > sma_200 and rvol_below_median > 0.5",
        "exit": "rvol_above_median > 0.5 or close < sma_200",
        "rationale": "PROXY for fear: step aside when realized vol elevated.",
        "expected": "Same family as vol_filter; labeled for meta.",
    },
    {
        "slug": "euphoria_extension_flat",
        "taxonomy": "sentiment_proxy",
        "entry": "close > sma_200 and price_z_20 < 2",
        "exit": "price_z_20 > 2.5 or close < sma_200",
        "rationale": "PROXY euphoria: exit extreme upside extensions.",
        "expected": "May cut winners; economic story thin.",
    },
    # ----- ONCHAIN PROXY (3) — activity via volume, NOT chain data -----
    {
        "slug": "activity_high_trend",
        "taxonomy": "onchain_proxy",
        "entry": "vol_ratio_20 > 1.2 and close > sma_100",
        "exit": "close < sma_100",
        "rationale": "PROXY for network activity using relative volume (not true on-chain).",
        "expected": "Honest proxy; should not be marketed as on-chain edge.",
    },
    {
        "slug": "activity_low_accumulation",
        "taxonomy": "onchain_proxy",
        "entry": "vol_ratio_20 < 0.8 and close > sma_200 and ret_20 > 0",
        "exit": "close < sma_200 or ret_20 < 0",
        "rationale": "PROXY quiet accumulation narrative.",
        "expected": "Storytelling risk; expect fail or weak.",
    },
    {
        "slug": "activity_thrust_mom",
        "taxonomy": "onchain_proxy",
        "entry": "vol_z_60 > 1 and ret_20 > 0",
        "exit": "ret_20 < 0",
        "rationale": "PROXY sustained activity + momentum.",
        "expected": "Overlaps volume+momentum meta family.",
    },
    # ----- FUNDING PROXY (3) — risk appetite via vol/trend, NOT perp funding -----
    {
        "slug": "risk_on_low_vol_trend",
        "taxonomy": "funding_proxy",
        "entry": "close > sma_200 and rvol_below_median > 0.5",
        "exit": "close < sma_200 or rvol_above_median > 0.5",
        "rationale": "PROXY for risk-on (calm trend) without perpetual funding rates.",
        "expected": "True funding requires futures PIT series (future work).",
    },
    {
        "slug": "risk_off_skip",
        "taxonomy": "funding_proxy",
        "entry": "close > sma_50 and rvol_20 < 0.8",
        "exit": "rvol_20 > 1.0 or close < sma_50",
        "rationale": "PROXY: avoid 'crowded leverage' regimes via high rvol threshold.",
        "expected": "Arbitrary thresholds; fragility.",
    },
    {
        "slug": "leverage_stress_flat",
        "taxonomy": "funding_proxy",
        "entry": "mom_pos_20 > 0.5 and rvol_below_median > 0.5",
        "exit": "rvol_above_median > 0.5 or mom_pos_20 < 0.5",
        "rationale": "PROXY: hold momentum only when vol not stressed.",
        "expected": "Not true funding; meta-label for research ops.",
    },
    # =====================================================================
    # WAVE 2 — Phase 2 signal discovery expansion (pre-registered grids)
    # Still OHLCV-only. Goal: volume of honest tests, not forced winners.
    # =====================================================================
    # --- Donchian / breakout (trend) ---
    {
        "slug": "donch20_breakout",
        "taxonomy": "trend",
        "entry": "above_donch_20 > 0.5",
        "exit": "below_donch_20 > 0.5",
        "rationale": "20-bar Donchian breakout (prior channel only).",
        "expected": "Classic turtle-style; few signals; costs matter.",
    },
    {
        "slug": "donch55_breakout",
        "taxonomy": "trend",
        "entry": "above_donch_55 > 0.5",
        "exit": "below_donch_55 > 0.5",
        "rationale": "55-bar Donchian breakout.",
        "expected": "Sparser than 20; well-known.",
    },
    {
        "slug": "donch100_breakout",
        "taxonomy": "trend",
        "entry": "above_donch_100 > 0.5",
        "exit": "below_donch_100 > 0.5",
        "rationale": "100-bar Donchian breakout.",
        "expected": "Very few trades; min_trades risk.",
    },
    {
        "slug": "donch20_with_sma200",
        "taxonomy": "trend",
        "entry": "above_donch_20 > 0.5 and close > sma_200",
        "exit": "below_donch_20 > 0.5 or close < sma_200",
        "rationale": "Donchian 20 only in long-term uptrend.",
        "expected": "Filters short side of channel noise.",
    },
    {
        "slug": "donch55_lowvol",
        "taxonomy": "composite",
        "entry": "above_donch_55 > 0.5 and rvol_below_median > 0.5",
        "exit": "below_donch_55 > 0.5",
        "rationale": "Breakout + low vol filter.",
        "expected": "May starve trades.",
    },
    # --- ATR trail ---
    {
        "slug": "atr_trail_trend",
        "taxonomy": "trend",
        "entry": "close > sma_100 and above_atr_trail > 0.5",
        "exit": "above_atr_trail < 0.5 or close < sma_100",
        "rationale": "Hold when above causal 2×ATR trail and medium trend.",
        "expected": "Path-dependent trail proxy; test integrity of feature.",
    },
    {
        "slug": "ema50_atr_exit",
        "taxonomy": "trend",
        "entry": "close > ema_50",
        "exit": "close < ema_50 or above_atr_trail < 0.5",
        "rationale": "EMA50 trend with ATR trail soft exit.",
        "expected": "Extra exit may increase churn.",
    },
    # --- Momentum grid ---
    {
        "slug": "mom_30_pos",
        "taxonomy": "momentum",
        "entry": "ret_30 > 0",
        "exit": "ret_30 < 0",
        "rationale": "30-day sign momentum.",
        "expected": "Between 20 and 60 horizons.",
    },
    {
        "slug": "mom_90_pos",
        "taxonomy": "momentum",
        "entry": "ret_90 > 0",
        "exit": "ret_90 < 0",
        "rationale": "90-day sign momentum.",
        "expected": "Slow; fewer flips.",
    },
    {
        "slug": "mom_30_strong",
        "taxonomy": "momentum",
        "entry": "ret_30 > 0.08",
        "exit": "ret_30 < 0",
        "rationale": "Require +8% 30d thrust.",
        "expected": "Late entry bias.",
    },
    {
        "slug": "mom_90_strong",
        "taxonomy": "momentum",
        "entry": "ret_90 > 0.15",
        "exit": "ret_90 < 0",
        "rationale": "Require +15% 90d thrust.",
        "expected": "Very late; sparse.",
    },
    {
        "slug": "mom_accel_pos",
        "taxonomy": "momentum",
        "entry": "mom_accel_20_60 > 0 and ret_20 > 0",
        "exit": "mom_accel_20_60 < 0 or ret_20 < 0",
        "rationale": "Momentum acceleration + positive short mom.",
        "expected": "Noisier; may fail costs.",
    },
    {
        "slug": "mom_accel_10_30",
        "taxonomy": "momentum",
        "entry": "mom_accel_10_30 > 0 and close > sma_50",
        "exit": "mom_accel_10_30 < 0 or close < sma_50",
        "rationale": "Fast acceleration with intermediate trend.",
        "expected": "Fragile.",
    },
    {
        "slug": "vol_adj_mom20",
        "taxonomy": "momentum",
        "entry": "ret_20 > 0 and rvol_below_median > 0.5",
        "exit": "ret_20 < 0",
        "rationale": "Vol-adjusted (filter) 20d momentum.",
        "expected": "Related to mom_skip_high_vol family.",
    },
    {
        "slug": "vol_adj_mom60",
        "taxonomy": "momentum",
        "entry": "ret_60 > 0 and rvol_below_median > 0.5",
        "exit": "ret_60 < 0",
        "rationale": "Vol-adjusted 60d momentum.",
        "expected": "Slower vol-filtered mom.",
    },
    {
        "slug": "mom90_trend200",
        "taxonomy": "composite",
        "entry": "ret_90 > 0 and close > sma_200",
        "exit": "ret_90 < 0 or close < sma_200",
        "rationale": "Long mom + long trend stack.",
        "expected": "Heavy beta; excess vs B&H critical.",
    },
    {
        "slug": "mom30_trend100",
        "taxonomy": "composite",
        "entry": "ret_30 > 0 and close > sma_100",
        "exit": "ret_30 < 0 or close < sma_100",
        "rationale": "Medium mom + medium trend.",
        "expected": "Common quant stack.",
    },
    # --- Volume wave ---
    {
        "slug": "vol_z_break_sma50",
        "taxonomy": "volume",
        "entry": "vol_z_20 > 1.5 and close > sma_50",
        "exit": "close < sma_50",
        "rationale": "Unusual volume + intermediate trend.",
        "expected": "Breakout false-positive risk.",
    },
    {
        "slug": "vol_z_break_sma200",
        "taxonomy": "volume",
        "entry": "vol_z_20 > 1.0 and close > sma_200",
        "exit": "close < sma_200",
        "rationale": "Elevated volume in long uptrend.",
        "expected": "Participation filter.",
    },
    {
        "slug": "vol_ratio_trend100",
        "taxonomy": "volume",
        "entry": "vol_ratio_20 > 1.3 and close > sma_100",
        "exit": "close < sma_100",
        "rationale": "Relative volume thrust + trend.",
        "expected": "Overlaps activity proxies.",
    },
    {
        "slug": "quiet_volume_mom",
        "taxonomy": "volume",
        "entry": "vol_z_20 < 0 and ret_20 > 0 and close > sma_50",
        "exit": "ret_20 < 0 or close < sma_50",
        "rationale": "Quiet volume continuation.",
        "expected": "Weak mechanism.",
    },
    {
        "slug": "vol60_mom60",
        "taxonomy": "volume",
        "entry": "vol_z_60 > 0.5 and ret_60 > 0",
        "exit": "ret_60 < 0",
        "rationale": "Sustained volume + medium momentum.",
        "expected": "Composite volume-mom.",
    },
    # --- Mean reversion wave ---
    {
        "slug": "fade_z20_m1",
        "taxonomy": "mean_reversion",
        "entry": "price_z_20 < -1.0 and close > sma_100",
        "exit": "price_z_20 > 0 or close < sma_100",
        "rationale": "Mild dip buy vs 20d z in uptrend.",
        "expected": "Crypto may not mean-revert.",
    },
    {
        "slug": "fade_z20_m2",
        "taxonomy": "mean_reversion",
        "entry": "price_z_20 < -2.0 and close > sma_200",
        "exit": "price_z_20 > -0.5 or close < sma_200",
        "rationale": "Deep 20d underextension in long uptrend.",
        "expected": "Rare; knife risk.",
    },
    {
        "slug": "fade_dist20_5pct",
        "taxonomy": "mean_reversion",
        "entry": "dist_sma_20 < -0.05 and close > sma_200",
        "exit": "dist_sma_20 > 0 or close < sma_200",
        "rationale": "5% below SMA20 dip-buy in bull.",
        "expected": "Mild MR.",
    },
    {
        "slug": "fade_dist50_12pct",
        "taxonomy": "mean_reversion",
        "entry": "dist_sma_50 < -0.12 and close > sma_200",
        "exit": "dist_sma_50 > 0 or close < sma_200",
        "rationale": "Deep SMA50 pullback in bull.",
        "expected": "Crash risk if trend fails.",
    },
    {
        "slug": "avoid_overext_only",
        "taxonomy": "mean_reversion",
        "entry": "close > sma_200 and price_z_20 < 1.0",
        "exit": "close < sma_200 or price_z_20 > 1.5",
        "rationale": "Trend but skip moderate upside extension.",
        "expected": "May cut winners early.",
    },
    # --- Vol regime wave ---
    {
        "slug": "long_only_rvol_declining",
        "taxonomy": "vol_filter",
        "entry": "rvol_20_chg < 0 and close > sma_50",
        "exit": "rvol_20_chg > 0.1 or close < sma_50",
        "rationale": "Long when vol declining + mild trend.",
        "expected": "Noisy vol-change signal.",
    },
    {
        "slug": "high_vol_mom_only",
        "taxonomy": "vol_filter",
        "entry": "rvol_above_median > 0.5 and ret_20 > 0",
        "exit": "ret_20 < 0",
        "rationale": "Only take momentum in high-vol half.",
        "expected": "Opposite of low-vol filters.",
    },
    {
        "slug": "low_vol_sma50",
        "taxonomy": "vol_filter",
        "entry": "rvol_below_median > 0.5 and close > sma_50",
        "exit": "rvol_above_median > 0.5 or close < sma_50",
        "rationale": "SMA50 trend gated by low vol.",
        "expected": "Common vol-timing stack.",
    },
    {
        "slug": "atr_pct_calm_long",
        "taxonomy": "vol_filter",
        "entry": "atr_pct < 0.04 and close > sma_100",
        "exit": "atr_pct > 0.07 or close < sma_100",
        "rationale": "Calm ATR% + medium trend.",
        "expected": "Threshold fragile.",
    },
    # --- Calendar / structure wave ---
    {
        "slug": "weekday_mom20",
        "taxonomy": "calendar",
        "entry": "is_weekend < 0.5 and ret_20 > 0",
        "exit": "is_weekend > 0.5 or ret_20 < 0",
        "rationale": "Momentum only on weekdays.",
        "expected": "Calendar folklore + mom.",
    },
    {
        "slug": "no_monday_hold",
        "taxonomy": "calendar",
        "entry": "is_monday < 0.5 and close > sma_100",
        "exit": "is_monday > 0.5 or close < sma_100",
        "rationale": "Flat Mondays in otherwise trend.",
        "expected": "Likely noise.",
    },
    {
        "slug": "month_start_mom",
        "taxonomy": "calendar",
        "entry": "is_month_start > 0.5 and ret_20 > 0",
        "exit": "is_month_start < 0.5 or ret_20 < 0",
        "rationale": "Month-start + short momentum.",
        "expected": "Sparse holds.",
    },
    {
        "slug": "avoid_month_end_mom",
        "taxonomy": "calendar",
        "entry": "is_month_end < 0.5 and ret_60 > 0",
        "exit": "is_month_end > 0.5 or ret_60 < 0",
        "rationale": "Medium mom avoiding month-end days.",
        "expected": "Weak prior.",
    },
    # --- Extra EMA / SMA grid ---
    {
        "slug": "ema20_long",
        "taxonomy": "trend",
        "entry": "close > ema_20",
        "exit": "close < ema_20",
        "rationale": "Fast EMA20 trend.",
        "expected": "High turnover.",
    },
    {
        "slug": "ema100_long",
        "taxonomy": "trend",
        "entry": "close > ema_100",
        "exit": "close < ema_100",
        "rationale": "EMA100 trend filter.",
        "expected": "Between 50 and 200 behavior.",
    },
    {
        "slug": "sma20_long",
        "taxonomy": "trend",
        "entry": "close > sma_20",
        "exit": "close < sma_20",
        "rationale": "Fast SMA20 trend.",
        "expected": "Churn + fees.",
    },
    {
        "slug": "ema20_50_cross",
        "taxonomy": "trend",
        "entry": "ema_20 > ema_50",
        "exit": "ema_20 < ema_50",
        "rationale": "EMA 20/50 cross.",
        "expected": "Classic; cost-sensitive.",
    },
    {
        "slug": "ema50_200_cross",
        "taxonomy": "trend",
        "entry": "ema_50 > ema_200",
        "exit": "ema_50 < ema_200",
        "rationale": "EMA 50/200 cross.",
        "expected": "Few trades.",
    },
    # --- Composite stacks ---
    {
        "slug": "donch20_mom20",
        "taxonomy": "composite",
        "entry": "above_donch_20 > 0.5 and ret_20 > 0",
        "exit": "below_donch_20 > 0.5 or ret_20 < 0",
        "rationale": "Breakout + short momentum confirm.",
        "expected": "Redundant signals often.",
    },
    {
        "slug": "sma200_vol_mom",
        "taxonomy": "composite",
        "entry": "close > sma_200 and rvol_below_median > 0.5 and ret_30 > 0",
        "exit": "close < sma_200 or ret_30 < 0",
        "rationale": "Trend + low vol + 30d mom.",
        "expected": "Kitchen-sink; sample risk.",
    },
    {
        "slug": "ema200_donch55",
        "taxonomy": "composite",
        "entry": "close > ema_200 and above_donch_55 > 0.5",
        "exit": "close < ema_200 or below_donch_55 > 0.5",
        "rationale": "Long EMA trend + medium Donchian.",
        "expected": "Sparse.",
    },
    # =====================================================================
    # WAVE 3 — economically motivated templates (guardrailed; not NN mining)
    # =====================================================================
    {
        "slug": "risk_on_trend_capital_flow",
        "taxonomy": "trend",
        "entry": "close > sma_200 and ret_60 > 0",
        "exit": "close < sma_200 or ret_60 < 0",
        "rationale": (
            "Risk-on capital and herding: investors chase established uptrends; "
            "price above long SMA plus positive medium momentum proxies ongoing "
            "inflows. Economic story is flow/herding, not magic SMA."
        ),
        "expected": (
            "May reduce cash drag vs pure SMA but still mostly beta; "
            "reject if no excess vs B&H or fails after costs/OOS."
        ),
    },
    {
        "slug": "vol_risk_premium_proxy",
        "taxonomy": "vol_filter",
        "entry": "rvol_below_median > 0.5 and close > sma_100",
        "exit": "rvol_above_median > 0.5 or close < sma_100",
        "rationale": (
            "Volatility risk premium / quiet-market preference: many allocators "
            "prefer risk when realized vol is subdued; low-vol regimes may "
            "coincide with more stable risk-bearing. Not a guarantee of premium."
        ),
        "expected": "Misses high-vol bull runs; reject if fee-fragile or low N.",
    },
    {
        "slug": "panic_rebound_long",
        "taxonomy": "mean_reversion",
        "entry": "ret_5 < -0.12 and close > sma_200",
        "exit": "ret_5 > 0.02 or close < sma_200",
        "rationale": (
            "Liquidity panic then rebound: sharp short-window selloffs in a "
            "secular uptrend can reflect temporary forced selling; mean reversion "
            "if long-term demand remains. Crash risk if trend is ending."
        ),
        "expected": "Few trades; often fails min_trades; knife-catch risk.",
    },
    {
        "slug": "breakout_participation",
        "taxonomy": "composite",
        "entry": "above_donch_55 > 0.5 and vol_z_20 > 0.5",
        "exit": "below_donch_55 > 0.5",
        "rationale": (
            "Information incorporation / attention: channel breakouts with "
            "elevated volume suggest broader participation, not thin prints. "
            "Classic market-structure story; still crowded and cost-sensitive."
        ),
        "expected": "Sparse signals; multiple-testing within breakout family.",
    },
    {
        "slug": "momentum_underreaction",
        "taxonomy": "momentum",
        "entry": "ret_90 > 0.1 and ret_20 > 0",
        "exit": "ret_20 < 0",
        "rationale": (
            "Underreaction / gradual information diffusion: large intermediate "
            "moves continue short-term if news is absorbed slowly. Behavioral "
            "finance prior; crypto may overreact instead."
        ),
        "expected": "Overlaps TSMOM family; selection bias high — confirmatory strict.",
    },
    {
        "slug": "avoid_vol_regime_shift",
        "taxonomy": "vol_filter",
        "entry": "close > sma_50 and rvol_20_chg < 0.05",
        "exit": "rvol_20_chg > 0.2 or close < sma_50",
        "rationale": (
            "Regime-shift risk: rising realized vol often marks transition to "
            "stress; reduce exposure when vol is accelerating even if price trend "
            "intact. Related to risk management, not pure return forecast."
        ),
        "expected": "May cut winners; test DD vs B&H tradeoff honestly.",
    },
]


def build_spec_dict(item: dict[str, Any], *, prefix: str = "hyp") -> dict[str, Any]:
    slug = item["slug"]
    tax = item["taxonomy"]
    return {
        "id": f"{prefix}_{slug}",
        "version": 1,
        "asset": "BTC/USDT",
        "timeframe": "1d",
        "taxonomy": tax,
        "family_id": f"family_{tax}",
        "entry": {"expression": item["entry"]},
        "exit": {"expression": item["exit"]},
        "rationale": item["rationale"],
        "expected_outcome": item["expected"],
        "feature_tags": [],
        "literature_refs": [],
    }


def write_catalog(out_dir: Path, *, prefix: str = "hyp") -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for item in CATALOG:
        spec = build_spec_dict(item, prefix=prefix)
        path = out_dir / f"{spec['id']}.yaml"
        path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        paths.append(path)
    # index
    index = {
        "count": len(CATALOG),
        "taxonomies": sorted({c["taxonomy"] for c in CATALOG}),
        "ids": [build_spec_dict(c, prefix=prefix)["id"] for c in CATALOG],
        "notes": (
            "sentiment_proxy / onchain_proxy / funding_proxy are HONEST PROXIES "
            "from OHLCV only — not social, chain, or perpetual funding data."
        ),
    }
    (out_dir / "INDEX.yaml").write_text(yaml.safe_dump(index, sort_keys=False))
    return paths


def catalog_count() -> int:
    return len(CATALOG)
