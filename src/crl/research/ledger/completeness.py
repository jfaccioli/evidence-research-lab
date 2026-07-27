"""Derived history completeness (never caller Boolean; never auto-COMPLETE).

PR4 evaluates artefact-digest / checkpoint / snapshot reconciliation gaps when
schema v4 tables are present. Missing verified legacy approval remains
blocking. PR5 derives external-anchor / off-machine-backup gaps from append-only
rows when schema v5+ is present (else hard-blocks as missing PR5). This module
must not mint promotable COMPLETE under null/default providers alone.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from crl.db.schema import connect_p1, get_schema_version
from crl.research.anchor.types import AnchorStatus, BackupStatus
from crl.research.artifacts.merkle import aggregate_digest_merkle, empty_merkle_root
from crl.research.artifacts.paths import require_artifact_root, resolve_under_root
from crl.research.ledger.hash_chain import verify_hash_chain
from crl.research.ledger.multiplicity import compute_multiplicity
from crl.research.programme.models import GovernanceCompleteness


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


def _pr5_anchor_backup_gaps(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    assessed_final_event_seq: Optional[int],
) -> tuple[list[str], list[str]]:
    """Derive PR5 gaps from append-only rows (tip-specific when seq known)."""
    gaps: list[str] = []
    blocks: list[str] = []
    version = get_schema_version(conn)
    if version is None or int(version) < 5:
        gaps.extend(
            (
                "missing_external_anchor_pr5",
                "missing_verified_off_machine_backup_pr5",
            )
        )
        blocks.append("pr5_external_anchor_or_off_machine_backup_missing")
        return gaps, blocks

    if assessed_final_event_seq is None:
        # No concrete tip: cannot claim anchor/backup authority.
        gaps.append("missing_assessed_tip_for_pr5_authority")
        gaps.append("missing_external_anchor_pr5")
        gaps.append("missing_verified_off_machine_backup_pr5")
        blocks.append("pr5_external_anchor_or_off_machine_backup_missing")
        return gaps, blocks

    tip = int(assessed_final_event_seq)
    rl = str(research_lineage_id).strip()
    anchor_row = conn.execute(
        """
        SELECT status FROM external_anchors
        WHERE research_lineage_id = ? AND final_event_seq = ?
        ORDER BY registration_event_seq DESC
        LIMIT 1
        """,
        (rl, tip),
    ).fetchone()
    if anchor_row is None or str(anchor_row[0]) != AnchorStatus.ANCHORED.value:
        gaps.append("missing_external_anchor_pr5")
        blocks.append("pr5_external_anchor_missing_or_pending")

    backup_row = conn.execute(
        """
        SELECT status FROM off_machine_backups
        WHERE research_lineage_id = ? AND final_event_seq = ?
        ORDER BY registration_event_seq DESC
        LIMIT 1
        """,
        (rl, tip),
    ).fetchone()
    if (
        backup_row is None
        or str(backup_row[0]) != BackupStatus.BACKUP_VERIFIED.value
    ):
        gaps.append("missing_verified_off_machine_backup_pr5")
        blocks.append("pr5_off_machine_backup_missing_or_unverified")

    if gaps:
        blocks.append("pr5_external_anchor_or_off_machine_backup_missing")
    return gaps, blocks


def _budget_debit_invariants(conn: sqlite3.Connection) -> list[str]:
    gaps: list[str] = []
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


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_physical_checkpoint_snapshot(
    conn: sqlite3.Connection,
    *,
    artifact_root: Path,
    checkpoint_id: str,
    final_seq: int,
    final_hash: str,
    ckpt_seq: int,
    snap_hash: str,
    snap_size: int,
    snap_rel: str,
    agg_root: str,
) -> list[str]:
    """Reopen snapshot under root; verify path/file/hash/size/tip/event."""
    gaps: list[str] = []
    # Containment without following a final-component symlink (pathlib resolve
    # would chase the link and mis-classify escapes as path_invalid).
    try:
        from crl.research.artifacts.paths import normalize_member_path

        rel = normalize_member_path(str(snap_rel))
        root_res = artifact_root.resolve()
        snap_path = root_res.joinpath(*rel.split("/"))
        root_s = str(root_res)
        cand_s = str(snap_path)
        if cand_s != root_s and not cand_s.startswith(root_s + os.sep):
            gaps.append("checkpoint_snapshot_path_invalid")
            return gaps
    except Exception:
        gaps.append("checkpoint_snapshot_path_invalid")
        return gaps

    if snap_path.is_symlink() or os.path.lexists(snap_path) and os.path.islink(
        snap_path
    ):
        gaps.append("checkpoint_snapshot_is_symlink")
        return gaps
    try:
        st = os.lstat(snap_path)
    except FileNotFoundError:
        gaps.append("checkpoint_snapshot_missing")
        return gaps
    except OSError:
        gaps.append("checkpoint_snapshot_unreadable")
        return gaps
    if not stat.S_ISREG(st.st_mode):
        gaps.append("checkpoint_snapshot_not_regular_file")
        return gaps
    if int(st.st_size) != int(snap_size):
        gaps.append("checkpoint_snapshot_size_mismatch")
    try:
        recomputed = _file_sha256(snap_path)
    except OSError:
        gaps.append("checkpoint_snapshot_unreadable")
        return gaps
    if recomputed != str(snap_hash):
        gaps.append("checkpoint_snapshot_hash_mismatch")

    # Trusted open requires a regular non-symlink path under the root.
    try:
        trusted_path = resolve_under_root(artifact_root, snap_rel)
    except Exception:
        gaps.append("checkpoint_snapshot_path_invalid")
        return gaps
    try:
        snap_conn = connect_p1(trusted_path, readonly=True)
    except Exception:
        gaps.append("checkpoint_snapshot_trusted_open_failed")
        return gaps
    try:
        tip = snap_conn.execute(
            """
            SELECT event_seq, event_hash
            FROM ledger_events
            ORDER BY event_seq DESC
            LIMIT 1
            """
        ).fetchone()
        if tip is None:
            if int(final_seq) != 0:
                gaps.append("checkpoint_snapshot_tip_mismatch")
        else:
            if int(tip[0]) != int(final_seq) or str(tip[1]) != str(final_hash):
                gaps.append("checkpoint_snapshot_tip_mismatch")
        # Snapshot must not contain the checkpoint event itself.
        ckpt_in_snap = snap_conn.execute(
            """
            SELECT 1 FROM ledger_events
            WHERE event_seq = ? OR event_type = 'checkpoint_recorded'
            LIMIT 1
            """,
            (int(ckpt_seq),),
        ).fetchone()
        if ckpt_in_snap is not None and int(final_seq) >= 0:
            # Only flag if checkpoint event leaked into the snapshot tip window.
            if snap_conn.execute(
                "SELECT 1 FROM ledger_events WHERE event_seq = ?",
                (int(ckpt_seq),),
            ).fetchone():
                gaps.append("checkpoint_snapshot_contains_checkpoint_event")
    finally:
        snap_conn.close()

    # Live ledger: checkpoint_event_seq must be checkpoint_recorded with payload.
    ev = conn.execute(
        """
        SELECT event_type, payload_json
        FROM ledger_events
        WHERE event_seq = ?
        """,
        (int(ckpt_seq),),
    ).fetchone()
    if ev is None:
        gaps.append("checkpoint_event_missing")
        return gaps
    if str(ev[0]) != "checkpoint_recorded":
        gaps.append("checkpoint_event_type_mismatch")
        return gaps
    try:
        payload = json.loads(str(ev[1]))
    except json.JSONDecodeError:
        gaps.append("checkpoint_event_payload_invalid")
        return gaps
    if not isinstance(payload, dict):
        gaps.append("checkpoint_event_payload_invalid")
        return gaps
    expected_fields = {
        "checkpoint_id": checkpoint_id,
        "final_event_seq": int(final_seq),
        "final_event_hash": str(final_hash),
        "database_snapshot_hash": str(snap_hash),
        "artifact_aggregate_merkle_root": str(agg_root),
        "snapshot_relative_path": str(snap_rel),
        "snapshot_byte_size": int(snap_size),
        "is_local_only": True,
        "is_authoritative": False,
    }
    for key, expected in expected_fields.items():
        actual = payload.get(key)
        if key in ("final_event_seq", "snapshot_byte_size"):
            try:
                actual = int(actual)
            except (TypeError, ValueError):
                gaps.append("checkpoint_event_payload_mismatch")
                break
        if actual != expected:
            gaps.append("checkpoint_event_payload_mismatch")
            break
    return gaps


def _artifact_and_checkpoint_gaps(
    conn: sqlite3.Connection,
    *,
    artifact_root: Optional[str | Path],
) -> list[str]:
    """Derivable PR4 reconciliation checks (never accepts caller Booleans)."""
    gaps: list[str] = []
    if not _table_exists(conn, "artifact_digests"):
        gaps.append("missing_artifact_bundle_digests_pr4")
        gaps.append("missing_post_event_checkpoints_pr4")
        gaps.append("missing_consistent_db_snapshot_hashes_pr4")
        return gaps

    # Completed trials without the exact immutable completion link.
    completed_without_link = conn.execute(
        """
        SELECT DISTINCT tse.trial_id
        FROM trial_state_events tse
        WHERE tse.execution_state = 'completed'
          AND NOT EXISTS (
              SELECT 1
              FROM trial_completion_links l
              WHERE l.trial_id = tse.trial_id
                AND l.completion_event_seq = tse.event_seq
                AND l.state_event_id = tse.state_event_id
          )
        """
    ).fetchall()
    if completed_without_link:
        gaps.append("completed_trials_without_exact_completion_link")

    # Completion links that do not bind a registered run artefact for the trial.
    bad_links = conn.execute(
        """
        SELECT l.trial_id
        FROM trial_completion_links l
        LEFT JOIN artifact_digests ad ON ad.artifact_id = l.artifact_id
        WHERE ad.artifact_id IS NULL
           OR ad.bundle_kind <> 'run'
           OR ad.trial_id <> l.trial_id
           OR ad.run_id <> l.run_id
           OR ad.registration_event_seq <> l.registration_event_seq
        """
    ).fetchall()
    if bad_links:
        gaps.append("completion_link_artifact_binding_mismatch")

    # Digest/event linkage mismatches.
    digest_event_mismatch = conn.execute(
        """
        SELECT ad.artifact_id
        FROM artifact_digests ad
        LEFT JOIN ledger_events le ON le.event_seq = ad.registration_event_seq
        WHERE le.event_seq IS NULL
           OR le.event_type <> 'artifact_bundle_sealed'
        """
    ).fetchall()
    if digest_event_mismatch:
        gaps.append("artifact_digest_event_linkage_mismatch")

    # Supersession errors: correction flag without supersession event, or
    # supersession event without matching correction row.
    bad_corrections = conn.execute(
        """
        SELECT ad.artifact_id
        FROM artifact_digests ad
        WHERE ad.is_correction = 1
          AND (
              ad.supersedes_artifact_id IS NULL
              OR NOT EXISTS (
                  SELECT 1 FROM artifact_digests prior
                  WHERE prior.artifact_id = ad.supersedes_artifact_id
              )
              OR NOT EXISTS (
                  SELECT 1 FROM ledger_events le
                  WHERE le.event_type = 'artifact_bundle_supersession'
                    AND le.payload_json LIKE '%' || ad.artifact_id || '%'
              )
          )
        """
    ).fetchall()
    if bad_corrections:
        gaps.append("artifact_supersession_errors")

    # Checkpoint tip/hash mismatches vs ledger + physical snapshot checks.
    if not _table_exists(conn, "checkpoints"):
        gaps.append("missing_post_event_checkpoints_pr4")
    else:
        ckpt_rows = conn.execute(
            """
            SELECT checkpoint_id, final_event_seq, final_event_hash,
                   checkpoint_event_seq, database_snapshot_hash,
                   artifact_aggregate_merkle_root, is_authoritative,
                   snapshot_byte_size, snapshot_relative_path
            FROM checkpoints
            """
        ).fetchall()
        for row in ckpt_rows:
            (
                ckpt_id,
                final_seq,
                final_hash,
                ckpt_seq,
                snap_hash,
                agg_root,
                is_auth,
                snap_size,
                snap_rel,
            ) = row
            if int(is_auth) != 0:
                gaps.append("local_checkpoint_marked_authoritative")
            if int(ckpt_seq) != int(final_seq) + 1:
                gaps.append("checkpoint_event_seq_not_after_tip")
            if int(final_seq) == 0:
                tip_ok = True
            else:
                tip = conn.execute(
                    """
                    SELECT event_hash FROM ledger_events WHERE event_seq = ?
                    """,
                    (int(final_seq),),
                ).fetchone()
                tip_ok = tip is not None and str(tip[0]) == str(final_hash)
                if not tip_ok:
                    gaps.append("checkpoint_tip_hash_mismatch")
            # Recompute aggregate of distinct artefact identities at/before tip.
            digests = [
                (str(r[0]), str(r[1]))
                for r in conn.execute(
                    """
                    SELECT artifact_id, merkle_root FROM artifact_digests
                    WHERE registration_event_seq <= ?
                    ORDER BY artifact_id
                    """,
                    (int(final_seq),),
                ).fetchall()
            ]
            expected_agg = (
                empty_merkle_root()
                if not digests
                else aggregate_digest_merkle(digests)
            )
            if str(agg_root) != expected_agg:
                gaps.append("checkpoint_artifact_aggregate_mismatch")

            if artifact_root is None:
                gaps.append("physical_snapshot_verification_unknown")
            else:
                try:
                    root = require_artifact_root(artifact_root)
                except Exception:
                    gaps.append("invalid_artifact_root_for_reconciliation")
                    continue
                gaps.extend(
                    _verify_physical_checkpoint_snapshot(
                        conn,
                        artifact_root=root,
                        checkpoint_id=str(ckpt_id),
                        final_seq=int(final_seq),
                        final_hash=str(final_hash),
                        ckpt_seq=int(ckpt_seq),
                        snap_hash=str(snap_hash),
                        snap_size=int(snap_size),
                        snap_rel=str(snap_rel),
                        agg_root=str(agg_root),
                    )
                )

        # Local checkpoints are never sufficient for promotion authority.
        gaps.append("local_checkpoints_non_authoritative")

    # Filesystem orphans when artefact root supplied.
    if artifact_root is not None:
        try:
            root = require_artifact_root(artifact_root)
        except Exception:
            gaps.append("invalid_artifact_root_for_reconciliation")
            return gaps
        registered_roots = {
            str(r[0])
            for r in conn.execute(
                "SELECT relative_root FROM artifact_digests"
            ).fetchall()
        }
        runs_base = root / "artifacts" / "runs"
        if runs_base.is_dir() and not runs_base.is_symlink():
            orphan_run = False
            for run_dir in runs_base.iterdir():
                if not run_dir.is_dir() or run_dir.is_symlink():
                    continue
                # Exclusive identity layout: artifacts/runs/{run_id}/{artifact_id}
                for child in run_dir.iterdir():
                    if not child.is_dir() or child.is_symlink():
                        continue
                    rel = f"artifacts/runs/{run_dir.name}/{child.name}"
                    if rel not in registered_roots:
                        gaps.append("filesystem_orphan_bundle_directory")
                        orphan_run = True
                        break
                if orphan_run:
                    break
        cohorts_base = root / "artifacts" / "cohorts"
        if cohorts_base.is_dir() and not cohorts_base.is_symlink():
            orphan = False
            for cohort_dir in cohorts_base.iterdir():
                if not cohort_dir.is_dir() or cohort_dir.is_symlink():
                    continue
                for child in cohort_dir.iterdir():
                    if not child.is_dir() or child.is_symlink():
                        continue
                    rel = f"artifacts/cohorts/{cohort_dir.name}/{child.name}"
                    if rel not in registered_roots:
                        gaps.append("filesystem_orphan_bundle_directory")
                        orphan = True
                        break
                if orphan:
                    break
        # Registered digests with missing/mismatched filesystem content.
        for row in conn.execute(
            """
            SELECT artifact_id, merkle_root, relative_root FROM artifact_digests
            """
        ).fetchall():
            artifact_id, merkle, rel = str(row[0]), str(row[1]), str(row[2])
            try:
                path = resolve_under_root(root, rel)
            except Exception:
                gaps.append("registered_bundle_path_invalid")
                continue
            if path.is_symlink() or not path.is_dir():
                gaps.append("registered_bundle_missing_on_filesystem")
                continue
            try:
                from crl.research.artifacts.bundle import verify_sealed_bundle_dir

                receipt = verify_sealed_bundle_dir(
                    path, expected_relative_root=rel
                )
            except Exception:
                gaps.append("registered_bundle_verification_failed")
                continue
            if receipt.merkle_root != merkle or receipt.artifact_id != artifact_id:
                gaps.append("registered_bundle_digest_mismatch_on_disk")

    return gaps


def assess_completeness(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    governance_epoch_id: Optional[str] = None,
    cohort_id: Optional[str] = None,
    caller_claims_complete: Optional[bool] = None,
    artifact_root: Optional[str | Path] = None,
) -> CompletenessAssessment:
    """Derive completeness from reconciliation. Caller Booleans are ignored."""
    # Explicitly discard any caller completeness claim.
    _ = caller_claims_complete

    gaps: list[str] = []
    block_reasons: list[str] = []
    is_legacy = governance_epoch_id is None

    if is_legacy:
        gaps.append("legacy_era_never_complete")
        block_reasons.append("legacy_era_never_complete")

    chain = verify_hash_chain(conn)
    if not chain.ok:
        gaps.append("hash_chain_integrity_failure")
        block_reasons.append("hash_chain_integrity_failure")
        for err in chain.errors[:3]:
            gaps.append(f"hash_chain:{err}")

    gaps.extend(_budget_debit_invariants(conn))

    open_reserved = conn.execute(
        "SELECT COUNT(*) FROM holdouts WHERE state = 'RESERVED'"
    ).fetchone()[0]
    if int(open_reserved) > 0:
        gaps.append("open_reserved_holdouts")

    version = get_schema_version(conn)
    if version is None or int(version) < 4:
        gaps.append("missing_artifact_bundle_digests_pr4")
        gaps.append("missing_post_event_checkpoints_pr4")
        gaps.append("missing_consistent_db_snapshot_hashes_pr4")
        block_reasons.append("pr4_artifact_checkpoint_invariants_missing")
    else:
        pr4_gaps = _artifact_and_checkpoint_gaps(
            conn, artifact_root=artifact_root
        )
        gaps.extend(pr4_gaps)
        # Schema present but promotion still blocked by local-only checkpoints
        # and any reconciliation gaps (never COMPLETE at PR4).
        block_reasons.append("pr4_local_checkpoints_non_authoritative")
        if any(
            g.startswith("completed_")
            or g.startswith("artifact_")
            or g.startswith("checkpoint_")
            or g.startswith("registered_")
            or g.startswith("filesystem_")
            or g.startswith("physical_")
            or g.startswith("completion_")
            for g in pr4_gaps
        ):
            block_reasons.append("pr4_reconciliation_gaps")

    # PR5: derive tip-specific anchor/backup authority (never COMPLETE on null).
    # Anchor/backup *recording* appends new ledger events; those events must not
    # advance the scientific tip used for tip-specific authority lookups.
    assessed_tip: Optional[int] = None
    tip_row = conn.execute(
        """
        SELECT COALESCE(MAX(event_seq), 0) FROM ledger_events
        WHERE event_type NOT IN (
            'external_anchor_recorded',
            'off_machine_backup_recorded'
        )
        """
    ).fetchone()
    if tip_row is not None and int(tip_row[0]) > 0:
        assessed_tip = int(tip_row[0])
    pr5_gaps, pr5_blocks = _pr5_anchor_backup_gaps(
        conn,
        research_lineage_id=research_lineage_id,
        assessed_final_event_seq=assessed_tip,
    )
    gaps.extend(pr5_gaps)
    block_reasons.extend(pr5_blocks)

    census = compute_multiplicity(
        conn,
        research_lineage_id=research_lineage_id,
        cohort_id=cohort_id,
    )
    gaps.append("missing_verified_legacy_n_approval")
    block_reasons.append("missing_verified_legacy_n_approval")
    if census.governance_violations:
        gaps.append("open_governance_violations")
        block_reasons.append("open_governance_violations")

    # Never mint COMPLETE: PR5 blockers + missing verified legacy approval.
    if is_legacy:
        if census.legacy_bound_n is not None and chain.ok:
            completeness = GovernanceCompleteness.LEGACY_RECONSTRUCTED_CONSERVATIVELY
        else:
            completeness = GovernanceCompleteness.INCOMPLETE_UNBOUNDED
    else:
        completeness = GovernanceCompleteness.INCOMPLETE_KNOWN_GAPS

    assert completeness is not GovernanceCompleteness.COMPLETE

    return CompletenessAssessment(
        completeness=completeness,
        gaps=tuple(dict.fromkeys(gaps)),
        promotion_blocked=True,
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
    artifact_root: Optional[str | Path] = None,
) -> GovernanceCompleteness:
    """Public helper: completeness enum only (never COMPLETE at PR4)."""
    return assess_completeness(
        conn,
        research_lineage_id=research_lineage_id,
        governance_epoch_id=governance_epoch_id,
        artifact_root=artifact_root,
    ).completeness
