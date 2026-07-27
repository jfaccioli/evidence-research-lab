"""Canonical economic mechanisms for coverage analysis.

Keywords are intentionally **strict** so multi-label inflation does not
declare every SMA rule as every mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mechanism:
    id: str
    name: str
    description: str
    typical_taxonomies: tuple[str, ...]
    keywords: tuple[str, ...]  # match rationale + id primarily; rules secondary


MECHANISMS: list[Mechanism] = [
    Mechanism(
        "herding_trend",
        "Herding / risk-on trend following",
        "Capital chases established price trends; SMA/EMA as flow proxies.",
        ("trend", "composite"),
        ("herd", "risk-on", "capital flow", "inflow", "sma200", "sma_200", "ema_200", "golden"),
    ),
    Mechanism(
        "breakout_attention",
        "Breakout + attention / participation",
        "New highs with volume reflect information incorporation.",
        ("trend", "composite", "volume"),
        ("donch", "breakout", "channel break", "participation breakout"),
    ),
    Mechanism(
        "tsmom_underreaction",
        "Time-series momentum / underreaction",
        "Gradual diffusion of information; intermediate returns continue.",
        ("momentum", "composite"),
        ("momentum", "underreaction", "tsmom", "ret_30", "ret_60", "ret_90", "mom_"),
    ),
    Mechanism(
        "vol_risk_premium",
        "Volatility risk preference / quiet markets",
        "Agents prefer risk when realized vol is low.",
        ("vol_filter", "composite"),
        ("vol risk", "quiet market", "rvol_below", "low-vol", "low vol", "calm atr"),
    ),
    Mechanism(
        "vol_regime_shift",
        "Volatility regime-shift risk",
        "Rising vol marks stress transitions; reduce exposure.",
        ("vol_filter",),
        ("regime shift", "rvol_20_chg", "vol spike", "vol accelerat", "regime-shift"),
    ),
    Mechanism(
        "liquidity_panic_rebound",
        "Forced selling / panic rebound",
        "Sharp selloffs reverse when temporary liquidity demand fades.",
        ("mean_reversion",),
        ("panic", "rebound", "forced sell", "knife", "crash bounce"),
    ),
    Mechanism(
        "volume_confirmation",
        "Volume confirmation of price moves",
        "Moves without volume are less reliable; thrust needs participation.",
        ("volume", "onchain_proxy", "sentiment_proxy"),
        ("vol_z", "vol_ratio", "volume thrust", "unusual volume", "volume confirm"),
    ),
    Mechanism(
        "calendar_seasonality",
        "Calendar / seasonality microstructure",
        "Day-of-week or month-end effects from institutional calendars.",
        ("calendar",),
        ("weekend", "monday", "friday", "month_end", "month_start", "calendar", "weekday"),
    ),
    Mechanism(
        "funding_crowding",
        "Perpetual funding / leverage crowding (true series)",
        "Funding rate as cost of leverage and crowded positioning; PIT exchange series only.",
        ("funding_proxy", "composite"),
        (
            "funding_last",
            "funding_high",
            "funding_z_60",
            "funding_chg",
            "funding_sum_24h",
            "funding_neg",
            "funding_pos",
            "true funding",
            "perpetual funding",
            "usdt-m funding",
        ),
    ),
    Mechanism(
        "crowding_proxy",
        "Crowding / leverage stress proxy",
        "High-vol or crowded risk-on states precede unwind (proxy only).",
        ("funding_proxy", "vol_filter"),
        ("funding_proxy", "leverage stress", "crowding", "risk_off_skip"),
    ),
    Mechanism(
        "atr_risk_trail",
        "Volatility-scaled risk trailing",
        "Position held only when price respects ATR-based risk budget.",
        ("trend", "vol_filter"),
        ("atr_trail", "above_atr", "atr trail", "2atr"),
    ),
    Mechanism(
        "asymmetric_capture",
        "Asymmetric upside/downside capture vs B&H",
        "Rule aims to cut left-tail BTC path while keeping right-tail (insurance-like).",
        ("composite", "trend", "vol_filter"),
        ("asymmetric", "insurance-like", "left-tail", "left tail", "capture_vol", "asymmetric_capture"),
    ),
    Mechanism(
        "mean_reversion_cross_section_proxy",
        "Relative value / stretch vs own history only",
        "Extreme z-score stretches mean-revert when not in structural bear.",
        ("mean_reversion",),
        ("price_z", "dist_sma", "mean reversion", "fade_", "stretch", "underextension"),
    ),
    Mechanism(
        "slow_fast_disagreement",
        "Slow vs fast signal disagreement",
        "When short-horizon mom disagrees with long trend, edge may be in resolution.",
        ("momentum", "composite", "trend"),
        ("disagreement", "mom_accel", "slow_fast", "pullback-in", "fast mom"),
    ),
    Mechanism(
        "capacity_tiny_friction",
        "Tiny-capital friction realism",
        "Edges that only work with zero friction are invalid for 10–50 AUD.",
        ("other",),
        ("tiny-capital", "tiny capital", "min notional", "dust", "capacity_fit", "friction realism"),
    ),
]


MECH_BY_ID = {m.id: m for m in MECHANISMS}


def infer_mechanisms(text: str, *, taxonomy: str = "") -> list[str]:
    """Map free text to mechanism ids. Prefer explicit keywords; light taxonomy assist."""
    t = text.lower()
    hits: list[str] = []
    for m in MECHANISMS:
        if any(k in t for k in m.keywords):
            hits.append(m.id)
    # taxonomy assist only if nothing matched
    if not hits and taxonomy:
        tax = taxonomy.lower()
        for m in MECHANISMS:
            if tax in m.typical_taxonomies:
                hits.append(m.id)
                break
    if not hits:
        hits.append("unknown")
    return hits
