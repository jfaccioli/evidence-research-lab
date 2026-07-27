"""Authoritative Thesis Tree / evidence mode gates (fail closed)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from crl.research.ledger.completeness import (
    CompletenessAssessment,
    assess_completeness,
)
from crl.research.programme.models import GovernanceCompleteness


@dataclass(frozen=True)
class AuthorityDecision:
    """Whether a view may claim scientific authority."""

    authoritative: bool
    reasons: tuple[str, ...]
    completeness: Optional[GovernanceCompleteness]
    promotion_blocked: bool


def decide_authoritative_mode(
    assessment: CompletenessAssessment,
    *,
    force_non_authoritative: bool = False,
) -> AuthorityDecision:
    """Authoritative only when completeness is COMPLETE and promotion unblocked.

    Under current P1 defaults (null anchor, local-only checkpoints, missing
    verified legacy bound), this returns non-authoritative — correct.
    """
    reasons: list[str] = []
    if force_non_authoritative:
        reasons.append("force_non_authoritative")
    if assessment.completeness is not GovernanceCompleteness.COMPLETE:
        reasons.append(f"completeness={assessment.completeness.value}")
    if assessment.promotion_blocked:
        reasons.append("promotion_blocked")
        reasons.extend(list(assessment.promotion_block_reasons)[:8])
    if assessment.gaps:
        # Surface first few structural gaps for operators.
        for g in assessment.gaps[:6]:
            if g not in reasons:
                reasons.append(f"gap:{g}")
    ok = (
        not force_non_authoritative
        and assessment.completeness is GovernanceCompleteness.COMPLETE
        and not assessment.promotion_blocked
    )
    return AuthorityDecision(
        authoritative=ok,
        reasons=tuple(dict.fromkeys(reasons)),
        completeness=assessment.completeness,
        promotion_blocked=assessment.promotion_blocked,
    )


def refuse_authoritative_if_blocked(decision: AuthorityDecision) -> None:
    """Raise when a caller requests authoritative output but gates fail."""
    if not decision.authoritative:
        raise PermissionError(
            "authoritative Thesis Tree / evidence mode refused: "
            + "; ".join(decision.reasons[:12])
        )


def assess_authoritative_mode(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    governance_epoch_id: Optional[str] = None,
    artifact_root: Optional[str | Path] = None,
    force_non_authoritative: bool = True,
) -> AuthorityDecision:
    """Default Thesis Tree rebuild path: non-authoritative unless all gates pass.

    ``force_non_authoritative=True`` is the safe default for live CLI rebuilds
    until cutover explicitly opts into governed authoritative packaging.
    """
    assessment = assess_completeness(
        conn,
        research_lineage_id=research_lineage_id,
        governance_epoch_id=governance_epoch_id,
        artifact_root=artifact_root,
    )
    return decide_authoritative_mode(
        assessment,
        force_non_authoritative=force_non_authoritative,
    )
