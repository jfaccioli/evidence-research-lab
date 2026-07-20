"""Pure promotion / rejection gates — single primary metric + constraints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crl.shared.types import GateConfig, Metrics


@dataclass
class GateResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def evaluate_gates(
    metrics: Metrics,
    gates: GateConfig,
    *,
    train_sharpe: float | None = None,
    wf_positive_frac: float | None = None,
    bootstrap_sharpe_lo: float | None = None,
    skeptical_p: float | None = None,
    mc_dd_breach_frac: float | None = None,
    fragility_pass_frac: float | None = None,
    stress_sharpe: float | None = None,
    trust_score: float | None = None,
    min_trust: float = 0.7,
    regime_max_share: float | None = None,
    confirmatory: bool = False,
    reality_reject_reasons: list[str] | None = None,
    reality_warnings: list[str] | None = None,
    multiple_testing_ok: bool | None = None,
    multiple_testing_note: str | None = None,
    fragility_inconclusive: bool = False,
) -> GateResult:
    """Pass only if primary after-cost Sharpe clears floor AND constraints hold.

    Secondary metrics cannot alone flip reject → pass.
    Reality Checker rejects are hard failures (economic/execution implausibility).
    """
    reasons: list[str] = []
    warnings: list[str] = []

    if reality_reject_reasons:
        for r in reality_reject_reasons:
            reasons.append(f"reality: {r}")
    if reality_warnings:
        for w in reality_warnings:
            warnings.append(f"reality: {w}")

    if metrics.n_trades < gates.min_trades:
        reasons.append(
            f"n_trades {metrics.n_trades} < min_trades {gates.min_trades}"
        )

    # Primary metric
    if metrics.sharpe_after_cost < gates.sharpe_min:
        reasons.append(
            f"primary sharpe_after_cost {metrics.sharpe_after_cost:.3f} < {gates.sharpe_min}"
        )

    if metrics.max_drawdown > gates.max_drawdown:
        reasons.append(
            f"max_drawdown {metrics.max_drawdown:.3f} > {gates.max_drawdown}"
        )

    if train_sharpe is not None:
        gap = train_sharpe - metrics.sharpe_after_cost
        if gap > gates.overfit_gap_max:
            reasons.append(
                f"overfit_gap {gap:.3f} > {gates.overfit_gap_max}"
            )

    if wf_positive_frac is not None and wf_positive_frac < gates.wf_min_positive_fold_frac:
        reasons.append(
            f"wf_positive_frac {wf_positive_frac:.2f} < {gates.wf_min_positive_fold_frac}"
        )

    if bootstrap_sharpe_lo is not None and bootstrap_sharpe_lo < gates.bootstrap_ci_lower_sharpe_min:
        reasons.append(
            f"bootstrap sharpe CI lo {bootstrap_sharpe_lo:.3f} < {gates.bootstrap_ci_lower_sharpe_min}"
        )

    if skeptical_p is not None and skeptical_p < gates.skeptical_p_mean_trade_gt0_min:
        reasons.append(
            f"skeptical P(mean trade>0) {skeptical_p:.3f} < {gates.skeptical_p_mean_trade_gt0_min}"
        )

    if stress_sharpe is not None and stress_sharpe < 0:
        reasons.append(f"2x cost stress sharpe {stress_sharpe:.3f} < 0")

    if trust_score is not None and trust_score < min_trust:
        reasons.append(f"data trust_score {trust_score:.2f} < {min_trust}")

    if fragility_inconclusive:
        warnings.append(
            "fragility: no tunable parameters found — robustness untested (fail-closed for confirmatory)"
        )

    if confirmatory:
        if mc_dd_breach_frac is not None and mc_dd_breach_frac > gates.mc_max_dd_breach_frac:
            reasons.append(
                f"MC DD breach frac {mc_dd_breach_frac:.2f} > {gates.mc_max_dd_breach_frac}"
            )
        if fragility_inconclusive:
            reasons.append(
                "fragility inconclusive (no param neighborhood) — confirmatory requires explicit robustness"
            )
        elif fragility_pass_frac is not None and fragility_pass_frac < gates.fragility_min_pass_frac:
            reasons.append(
                f"fragility pass_frac {fragility_pass_frac:.2f} < {gates.fragility_min_pass_frac}"
            )
        if multiple_testing_ok is False:
            reasons.append(
                f"multiple-testing hygiene failed: {multiple_testing_note or 'see DSR/Bonferroni'}"
            )
    elif multiple_testing_ok is False:
        warnings.append(
            f"multiple-testing: {multiple_testing_note or 'family size suggests elevated false-discovery risk'}"
        )

    if regime_max_share is not None and regime_max_share > gates.regime_concentration_warn:
        warnings.append(
            f"regime concentration {regime_max_share:.2f} > {gates.regime_concentration_warn} "
            "(edge may be regime-specific — labeled, not auto-reject)"
        )

    return GateResult(
        passed=len(reasons) == 0,
        reasons=reasons,
        warnings=warnings,
        details={
            "primary": metrics.sharpe_after_cost,
            "n_trades": metrics.n_trades,
            "max_dd": metrics.max_drawdown,
        },
    )


# Future phases — pure functions only, never agent-writable
PHASE_ORDER = [
    "research",
    "expanded_research",
    "paper",
    "shadow",
    "tiny_live",
]


def can_promote(from_phase: str, to_phase: str, gate: GateResult) -> bool:
    if not gate.passed:
        return False
    try:
        i = PHASE_ORDER.index(from_phase)
        j = PHASE_ORDER.index(to_phase)
    except ValueError:
        return False
    return j == i + 1
