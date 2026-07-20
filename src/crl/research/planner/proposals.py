"""Hypothesis proposals optimised for information gain (not win rate)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crl.research.planner.analyze import RegistryAnalysis, _rule_fingerprint
from crl.research.planner.mechanisms import MECH_BY_ID
from crl.research.planner.score import InformationGainScore, score_information_gain
from crl.research.hypotheses.guardrails import validate_hypothesis_spec
from crl.shared.types import HypothesisSpec, RuleSpec, Taxonomy


@dataclass
class ResearchProposal:
    id: str
    mechanism_ids: list[str]
    taxonomy: str
    entry: str
    exit: str
    economic_rationale: str
    falsification_criteria: str
    why_different: str
    expected_failure_modes: str
    invalidates_assumption: str
    expected_value_if_true: str
    information_gain: InformationGainScore
    family_id: str = ""
    priority_rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "priority_rank": self.priority_rank,
            "mechanism_ids": self.mechanism_ids,
            "taxonomy": self.taxonomy,
            "entry": self.entry,
            "exit": self.exit,
            "economic_rationale": self.economic_rationale,
            "falsification_criteria": self.falsification_criteria,
            "why_different": self.why_different,
            "expected_failure_modes": self.expected_failure_modes,
            "invalidates_assumption": self.invalidates_assumption,
            "expected_value_if_true": self.expected_value_if_true,
            "family_id": self.family_id,
            "information_gain": self.information_gain.to_dict(),
        }

    def to_hypothesis_spec(self) -> HypothesisSpec:
        return HypothesisSpec(
            id=self.id,
            taxonomy=Taxonomy(self.taxonomy)
            if self.taxonomy in Taxonomy._value2member_map_
            else Taxonomy.OTHER,
            family_id=self.family_id or f"family_{self.mechanism_ids[0]}",
            entry=RuleSpec(expression=self.entry),
            exit=RuleSpec(expression=self.exit),
            rationale=self.economic_rationale,
            expected_outcome=self.falsification_criteria,
        )


# Library of *candidate* ideas the planner may emit if IG is high and not clones.
# Keep small; quality > quantity. Each targets a distinct mechanism.
_CANDIDATE_POOL: list[dict[str, Any]] = [
    {
        "slug": "asymmetric_capture_vol_gate",
        "mechanism_ids": ["asymmetric_capture", "vol_regime_shift"],
        "taxonomy": "composite",
        "entry": "close > sma_200 and rvol_20_chg < 0.1",
        "exit": "close < sma_100 or rvol_20_chg > 0.25",
        "economic_rationale": (
            "Insurance-like asymmetric capture: stay long BTC secular trend but "
            "exit early when realized-vol acceleration signals regime stress. "
            "Goal is left-tail reduction vs buy-and-hold, not higher CAGR."
        ),
        "falsification": (
            "Reject if after-cost Calmar/Sharpe not better on risk terms, or if "
            "excess vs B&H is non-positive with similar DD, or confirmatory fails."
        ),
        "why_different": (
            "Prior work mostly maximised raw trend/mom Sharpe. This targets "
            "explicit DD/path insurance vs B&H as the economic claim."
        ),
        "expected_failure_modes": (
            "Whipsaw in choppy vol; underperform strong high-vol bulls; low trade "
            "count if exits rare; fee drag on toggles."
        ),
        "invalidates_assumption": (
            "Invalidates 'simple trend filters cannot improve left-tail vs B&H "
            "after costs' if confirmatory risk metrics improve."
        ),
        "ev_if_true": (
            "High for tiny capital: surviving drawdowns matters more than peak "
            "CAGR when AUD is 10–50 and psychology/ops constraints bind."
        ),
    },
    {
        "slug": "slow_fast_mom_disagreement_resolve",
        "mechanism_ids": ["slow_fast_disagreement", "tsmom_underreaction"],
        "taxonomy": "momentum",
        "entry": "ret_90 > 0 and ret_10 < 0 and close > sma_200",
        "exit": "ret_10 > 0.03 or close < sma_200",
        "economic_rationale": (
            "Slow/fast disagreement: long-horizon momentum still positive (underreaction "
            "to major regime) while short-term pullback offers better entry. Resolution "
            "is re-acceleration of short mom within long uptrend."
        ),
        "falsification": (
            "Reject if entries are too rare (n_trades), if rebounds fail more than "
            "cash/B&H, or if only works in one bull window."
        ),
        "why_different": (
            "Catalog mom rules mostly require short mom > 0. This requires short mom "
            "< 0 inside a slow-up structure — opposite entry condition."
        ),
        "expected_failure_modes": (
            "Catching falling knives when 90d mom is stale; sparse signals; "
            "overlap with dip-buy mean reversion family."
        ),
        "invalidates_assumption": (
            "Invalidates 'momentum entries must be with-trend on all horizons' if "
            "pullback-in-slow-up works OOS after costs."
        ),
        "ev_if_true": (
            "Improves entry timing vs always-on slow mom; moderate EV if true."
        ),
    },
    {
        "slug": "stretch_fade_only_low_vol",
        "mechanism_ids": ["mean_reversion_cross_section_proxy", "vol_risk_premium"],
        "taxonomy": "mean_reversion",
        "entry": "price_z_20 < -1.5 and rvol_below_median > 0.5 and close > sma_200",
        "exit": "price_z_20 > 0 or rvol_above_median > 0.5 or close < sma_200",
        "economic_rationale": (
            "Liquidity dips in calm uptrends mean-revert; deep z-score stretches "
            "during low-vol regimes are more likely inventory/noise than regime change."
        ),
        "falsification": (
            "Reject on knife-catch losses in calm-before-crash, low N, or no edge "
            "after costs vs sitting in sma200 trend alone."
        ),
        "why_different": (
            "Combines stretch MR with mandatory low-vol filter and long SMA; prior "
            "MR tests often ignored vol state or used high-vol fades."
        ),
        "expected_failure_modes": (
            "Structural breaks start in 'calm'; sample starvation; multiple-testing "
            "within MR family."
        ),
        "invalidates_assumption": (
            "Invalidates 'BTC daily mean reversion is untradeable after costs in "
            "uptrends' if confirmatory passes with enough trades."
        ),
        "ev_if_true": "Moderate; adds a distinct MR+vol mechanism for the knowledge base.",
    },
    {
        "slug": "participation_breakout_55_strict",
        "mechanism_ids": ["breakout_attention"],
        "taxonomy": "composite",
        "entry": "above_donch_55 > 0.5 and vol_ratio_20 > 1.4 and ret_20 > 0",
        "exit": "below_donch_55 > 0.5 or ret_20 < 0",
        "economic_rationale": (
            "Attention/participation breakouts: channel exit with elevated relative "
            "volume and positive medium momentum indicates broad incorporation of news, "
            "not a thin wick."
        ),
        "falsification": (
            "Reject if sparse trades, if volume filter adds nothing vs bare Donchian, "
            "or confirmatory negative."
        ),
        "why_different": (
            "Stricter participation stack than prior donch/volume singles; explicit "
            "three-way confirmation to test whether stacking kills N or adds edge."
        ),
        "expected_failure_modes": "Over-constraint → low_sample; crowded breakout lore.",
        "invalidates_assumption": (
            "If still fails like bare Donchian, strengthens 'breakout lore exhausted "
            "on BTC daily' — high value null result."
        ),
        "ev_if_true": "Low-moderate trading EV; high IG as decisive null or rare pass.",
    },
    {
        "slug": "calendar_null_weekday_only_bh",
        "mechanism_ids": ["calendar_seasonality"],
        "taxonomy": "calendar",
        "entry": "is_weekend < 0.5",
        "exit": "is_weekend > 0.5",
        "economic_rationale": (
            "Institutional calendar: risk transfer differs weekend vs weekday even in "
            "24/7 crypto via TradFi desk coverage. Pure weekday long is a clean test "
            "of residual weekend risk premium/discount."
        ),
        "falsification": (
            "Reject if no excess vs full B&H after costs, or effect is pure noise in WF."
        ),
        "why_different": (
            "Prior calendar tests mixed calendar with trend filters. This isolates "
            "calendar alone so the mechanism can be retired cleanly if null."
        ),
        "expected_failure_modes": "No effect; high turnover at weekend boundaries; fees.",
        "invalidates_assumption": (
            "Invalidates or confirms 'weekend risk is a tradable BTC daily effect'."
        ),
        "ev_if_true": "If true, simple operational rule; if false, retire calendar family.",
    },
    {
        "slug": "high_vol_skip_is_not_enough",
        "mechanism_ids": ["vol_regime_shift", "herding_trend"],
        "taxonomy": "vol_filter",
        "entry": "close > sma_100 and rvol_20 < rvol_60",
        "exit": "close < sma_100 or rvol_20 > rvol_60",
        "economic_rationale": (
            "Relative vol state: short realized vol below long realized vol marks "
            "compressing risk; herding/trend more stable. Distinct from expanding-median "
            "filters already tested heavily."
        ),
        "falsification": (
            "Reject if identical outcomes to rvol_below_median family (redundant), "
            "or fails costs/OOS."
        ),
        "why_different": (
            "Uses rvol_20 vs rvol_60 cross, not expanding median — different definition "
            "of 'calm' to avoid retesting the same threshold story."
        ),
        "expected_failure_modes": "Collinear with existing vol filters; low novelty if correlated.",
        "invalidates_assumption": (
            "If fails like expanding-median filters, vol-timing on daily may be exhausted."
        ),
        "ev_if_true": "Moderate; diversifies vol-timing definition.",
    },
]


def generate_ranked_proposals(
    analysis: RegistryAnalysis,
    *,
    max_n: int = 5,
    min_ig: float = 0.35,
    prefix: str = "plan",
) -> list[ResearchProposal]:
    """Score pool against registry evidence; return top non-clone proposals."""
    ranked: list[ResearchProposal] = []
    exhausted = set(analysis.exhausted_families)

    for raw in _CANDIDATE_POOL:
        fp = _rule_fingerprint(raw["entry"], raw["exit"])
        mechs = list(raw["mechanism_ids"])
        # near exhausted if all mechs heavily covered and family-like retire
        near_ex = any(
            f.recommendation == "retire" and any(m in f.mechanisms for m in mechs)
            for f in analysis.families
        )
        ig = score_information_gain(
            mechanism_ids=mechs,
            rule_fingerprint=fp,
            analysis=analysis,
            invalidates_assumption=raw["invalidates_assumption"],
            expected_value_if_true=raw["ev_if_true"],
            near_exhausted_family=near_ex,
        )
        prop = ResearchProposal(
            id=f"{prefix}_{raw['slug']}",
            mechanism_ids=mechs,
            taxonomy=raw["taxonomy"],
            entry=raw["entry"],
            exit=raw["exit"],
            economic_rationale=raw["economic_rationale"],
            falsification_criteria=raw["falsification"],
            why_different=raw["why_different"],
            expected_failure_modes=raw["expected_failure_modes"],
            invalidates_assumption=raw["invalidates_assumption"],
            expected_value_if_true=raw["ev_if_true"],
            information_gain=ig,
            family_id=f"family_mech_{mechs[0]}",
        )
        # guardrail check
        g = validate_hypothesis_spec(prop.to_hypothesis_spec())
        if not g.ok:
            continue
        if ig.total < min_ig:
            continue
        if fp in analysis.explored_rule_fingerprints:
            continue
        ranked.append(prop)

    ranked.sort(key=lambda p: -p.information_gain.total)
    # diversity: limit per primary mechanism
    out: list[ResearchProposal] = []
    mech_used: dict[str, int] = {}
    for p in ranked:
        primary = p.mechanism_ids[0]
        if mech_used.get(primary, 0) >= 1 and len(out) > 0:
            # allow second only if IG very high
            if p.information_gain.total < 0.55:
                continue
        if len(out) >= max_n:
            break
        mech_used[primary] = mech_used.get(primary, 0) + 1
        p.priority_rank = len(out) + 1
        out.append(p)
    return out
