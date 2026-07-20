"""Guarded hypothesis drafting — expands search space without black boxes.

Does NOT auto-register or auto-backtest. Outputs structured candidates that
still must be written to catalog/YAML, pre-registered, then run exploratorily.

Standing order: every idea needs economic rationale + explicit rule.
"""

from __future__ import annotations

from typing import Any

from crl.research.hypotheses.guardrails import validate_hypothesis_spec
from crl.shared.types import HypothesisSpec, RuleSpec, Taxonomy


# Curated *templates* with real economic stories (not random mashups).
# Used to draft Wave-3+ families; human/catalog still freezes before test.
ECONOMIC_TEMPLATES: list[dict[str, Any]] = [
    {
        "slug": "risk_on_trend_capital_flow",
        "taxonomy": Taxonomy.TREND,
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
        "taxonomy": Taxonomy.VOL_FILTER,
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
        "taxonomy": Taxonomy.MEAN_REVERSION,
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
        "taxonomy": Taxonomy.COMPOSITE,
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
        "taxonomy": Taxonomy.MOMENTUM,
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
        "taxonomy": Taxonomy.VOL_FILTER,
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


def draft_from_templates(*, prefix: str = "hyp") -> list[HypothesisSpec]:
    """Return validated specs ready for catalog inclusion (not auto-run)."""
    out: list[HypothesisSpec] = []
    for t in ECONOMIC_TEMPLATES:
        spec = HypothesisSpec(
            id=f"{prefix}_{t['slug']}",
            taxonomy=t["taxonomy"],
            family_id=f"family_{t['taxonomy'].value}",
            entry=RuleSpec(expression=t["entry"]),
            exit=RuleSpec(expression=t["exit"]),
            rationale=t["rationale"],
            expected_outcome=t["expected"],
        )
        g = validate_hypothesis_spec(spec)
        if not g.ok:
            raise ValueError(f"Template {t['slug']} invalid: {g.errors}")
        out.append(spec)
    return out


def templates_as_catalog_items() -> list[dict[str, Any]]:
    """Shape for catalog.CATALOG append."""
    items = []
    for t in ECONOMIC_TEMPLATES:
        items.append(
            {
                "slug": t["slug"],
                "taxonomy": t["taxonomy"].value,
                "entry": t["entry"],
                "exit": t["exit"],
                "rationale": t["rationale"],
                "expected": t["expected"],
            }
        )
    return items
