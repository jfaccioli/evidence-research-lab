"""Derived history completeness (never caller Boolean; never auto-COMPLETE).

At PR3, PR4 artifact/checkpoint invariants are explicit known gaps, so this
module must not mint promotable COMPLETE. Legacy history can never be COMPLETE.
Proposed legacy N bounds are diagnostic only and never satisfy completeness.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from crl.research.programme.models import GovernanceCompleteness
from crl.research.ledger.hash_chain import verify_hash_chain
from crl.research.ledger.multiplicity import compute_multiplicity


@dataclass(frozen=True)
class CompletenessAssessment:
    """Reconciliation-derived completeness with explicit gap enumeration."""

    completeness: GovernanceCompleteness
    gaps: tuple[str, ...]
    promotion_blocked: bool
    promotion_block_reasons: tuple[str, ...]
    is_legacy_era: bool
    n_global: Optional[int]
    n_cohort: Optional[int]
    proposed_legacy_bound_n: Optional[int] = None


# Invariants that PR3 can evaluate.
_PR3_EVALUABLE = (
    "event_sequence_contiguous_hash_chain",
    "budget_debits_match_billable_trials",
    "verified_legacy_n_approval_present",
)

# Explicit PR4+ gaps that block COMPLETE until later PRs.
_PR4_GAPS = (
    "missing_artifact_bundle_digests_pr4",
    "missing_post_event_checkpoints_pr4",
    "missing_consistent_db_snapshot_hashes_pr4",
    "missing_external_anchor_or_off_machine_backup_pr4",
)


def _budget_debit_invariants(conn: sqlite3.Connection) -> list[str]:
    gaps: list[str] = []
    # Every billable trial has exactly one debit; non-billable have none.
    orphan_billable = conn.execute(
        """
        SELECT t.trial_id
        FROM trials t
        LEFT JOIN budget_debits d ON d.trial_id = t.trial_id
        WHERE t.billable = 1 AND d.trial_id IS NULL
        """
    ).fetchall()
    if orphan_billable:
        gaps.append("billable_trials_missing_budget_debit")
    extra = conn.execute(
        """
        SELECT d.trial_id
        FROM budget_debits d
        JOIN trials t ON t.trial_id = d.trial_id
        WHERE t.billable = 0
        """
    ).fetchall()
    if extra:
        gaps.append("non_billable_trials_have_budget_debit")
    # Debit event_seq must equal the trial registration event for atomic link.
    mismatched = conn.execute(
        """
        SELECT d.trial_id
        FROM budget_debits d
        JOIN trials t ON t.trial_id = d.trial_id
        WHERE d.event_seq <> t.registration_event_seq
        """
    ).fetchall()
    if mismatched:
        gaps.append("budget_debit_event_seq_mismatch")
    cross_lineage = conn.execute(
        """
        SELECT d.trial_id
        FROM budget_debits d
        JOIN budget_allocations a ON a.allocation_id = d.allocation_id
        JOIN trials t ON t.trial_id = d.trial_id
        WHERE a.research_lineage_id <> t.research_lineage_id
        """
    ).fetchall()
    if cross_lineage:
        gaps.append("budget_debit_research_lineage_mismatch")
    return gaps


def assess_completeness(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    governance_epoch_id: Optional[str] = None,
    cohort_id: Optional[str] = None,
    caller_claims_complete: Optional[bool] = None,
) -> CompletenessAssessment:
    """Derive completeness from reconciliation. Caller Booleans are ignored."""
    # Explicitly discard any caller completeness claim.
    _ = caller_claims_complete

    gaps: list[str] = []
    block_reasons: list[str] = []
    is_legacy = governance_epoch_id is None

    if is_legacy:
        # Legacy era can never become COMPLETE.
        gaps.append("legacy_era_never_complete")
        block_reasons.append("legacy_era_never_complete")

    chain = verify_hash_chain(conn)
    if not chain.ok:
        gaps.append("hash_chain_integrity_failure")
        block_reasons.append("hash_chain_integrity_failure")
        for err in chain.errors[:3]:
            gaps.append(f"hash_chain:{err}")

    gaps.extend(_budget_debit_invariants(conn))

    # Holdout RESERVED rows must eventually terminate (invariant 3) — report
    # open reservations as known operational gaps, not COMPLETE blockers alone.
    open_reserved = conn.execute(
        "SELECT COUNT(*) FROM holdouts WHERE state = 'RESERVED'"
    ).fetchone()[0]
    if int(open_reserved) > 0:
        gaps.append("open_reserved_holdouts")

    # PR4 invariants are always explicit gaps at PR3.
    gaps.extend(_PR4_GAPS)
    block_reasons.append("pr4_artifact_checkpoint_invariants_missing")

    census = compute_multiplicity(
        conn,
        research_lineage_id=research_lineage_id,
        cohort_id=cohort_id,
    )
    # Proposals never satisfy verified legacy approval.
    gaps.append("missing_verified_legacy_n_approval")
    block_reasons.append("missing_verified_legacy_n_approval")
    if census.governance_violations:
        gaps.append("open_governance_violations")
        block_reasons.append("open_governance_violations")

    # Never mint COMPLETE in PR3: PR4 gaps are always present.
    # A proposal alone never yields LEGACY_RECONSTRUCTED_CONSERVATIVELY.
    if is_legacy:
        if census.legacy_bound_n is not None and chain.ok:
            completeness = GovernanceCompleteness.LEGACY_RECONSTRUCTED_CONSERVATIVELY
        else:
            completeness = GovernanceCompleteness.INCOMPLETE_UNBOUNDED
    else:
        # Governed epoch: known gaps (including PR4) → INCOMPLETE_KNOWN_GAPS.
        completeness = GovernanceCompleteness.INCOMPLETE_KNOWN_GAPS

    assert completeness is not GovernanceCompleteness.COMPLETE

    return CompletenessAssessment(
        completeness=completeness,
        gaps=tuple(dict.fromkeys(gaps)),  # stable unique
        promotion_blocked=True,  # PR3 never enables promotion
        promotion_block_reasons=tuple(dict.fromkeys(block_reasons)),
        is_legacy_era=is_legacy,
        n_global=census.n_global,
        n_cohort=census.n_cohort,
        proposed_legacy_bound_n=census.proposed_legacy_bound_n,
    )


def derive_completeness_from_ledger(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    governance_epoch_id: Optional[str] = None,
) -> GovernanceCompleteness:
    """Public helper: completeness enum only (never COMPLETE at PR3)."""
    return assess_completeness(
        conn,
        research_lineage_id=research_lineage_id,
        governance_epoch_id=governance_epoch_id,
    ).completeness
