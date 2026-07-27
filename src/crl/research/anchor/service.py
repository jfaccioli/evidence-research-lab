"""Append-only recording of anchor and backup verification receipts."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Optional

from crl.research.anchor.base import AnchorProvider, OffMachineBackupVerifier
from crl.research.anchor.types import (
    AnchorError,
    AnchorReceipt,
    AnchorStatus,
    AnchorTarget,
    BackupStatus,
    BackupVerificationError,
    BackupVerificationReceipt,
    BackupVerificationRequest,
)
from crl.research.artifacts.paths import require_safe_path_component
from crl.research.ledger.events import append_event
from crl.research.ledger.hash_chain import LedgerHashError, canonical_json


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _sha256_hex(value: str, field: str) -> str:
    text = str(value).strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise AnchorError(f"{field} must be lowercase SHA-256 hex")
    return text


def record_anchor(
    conn: sqlite3.Connection,
    provider: AnchorProvider,
    target: AnchorTarget,
) -> tuple[AnchorReceipt, str, int]:
    """Call provider then append-only record (event + external_anchors row).

    Returns ``(receipt, anchor_id, registration_event_seq)``.
    """
    rl = str(target.research_lineage_id).strip()
    if not rl:
        raise AnchorError("research_lineage_id required")
    if int(target.final_event_seq) < 1:
        raise AnchorError("final_event_seq must be >= 1")
    tip_hash = _sha256_hex(target.final_event_hash, "final_event_hash")
    normalized = AnchorTarget(
        research_lineage_id=rl,
        final_event_seq=int(target.final_event_seq),
        final_event_hash=tip_hash,
        checkpoint_id=(
            str(target.checkpoint_id).strip()
            if target.checkpoint_id is not None and str(target.checkpoint_id).strip()
            else None
        ),
        database_snapshot_hash=(
            _sha256_hex(target.database_snapshot_hash, "database_snapshot_hash")
            if target.database_snapshot_hash
            else None
        ),
        artifact_aggregate_root=(
            _sha256_hex(target.artifact_aggregate_root, "artifact_aggregate_root")
            if target.artifact_aggregate_root
            else None
        ),
    )
    receipt = provider.anchor(normalized)
    if not isinstance(receipt.status, AnchorStatus):
        raise AnchorError("provider returned invalid status")
    if receipt.provider_id != provider.provider_id:
        raise AnchorError("provider_id mismatch on receipt")
    if receipt.external_ref is not None and (
        "secret" in str(receipt.external_ref).lower()
        or "token" in str(receipt.external_ref).lower()
        or "password" in str(receipt.external_ref).lower()
    ):
        raise AnchorError("external_ref must not look like a secret")

    anchor_id = require_safe_path_component(_new_id("anc"), field="anchor_id")
    payload = {
        "anchor_id": anchor_id,
        "provider_id": receipt.provider_id,
        "status": receipt.status.value,
        "research_lineage_id": normalized.research_lineage_id,
        "final_event_seq": normalized.final_event_seq,
        "final_event_hash": normalized.final_event_hash,
        "checkpoint_id": normalized.checkpoint_id,
        "database_snapshot_hash": normalized.database_snapshot_hash,
        "artifact_aggregate_root": normalized.artifact_aggregate_root,
        "external_ref": receipt.external_ref,
        "attested_at": receipt.attested_at,
        "detail": dict(receipt.detail),
    }
    try:
        event_seq, _event_hash = append_event(
            conn,
            event_type="external_anchor_recorded",
            payload=payload,
        )
        conn.execute(
            """
            INSERT INTO external_anchors(
                anchor_id, provider_id, status, research_lineage_id,
                final_event_seq, final_event_hash, checkpoint_id,
                database_snapshot_hash, artifact_aggregate_root,
                external_ref, registration_event_seq, attested_at, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                anchor_id,
                receipt.provider_id,
                receipt.status.value,
                normalized.research_lineage_id,
                normalized.final_event_seq,
                normalized.final_event_hash,
                normalized.checkpoint_id,
                normalized.database_snapshot_hash,
                normalized.artifact_aggregate_root,
                receipt.external_ref,
                event_seq,
                receipt.attested_at,
                canonical_json(dict(receipt.detail)),
            ),
        )
    except (sqlite3.Error, LedgerHashError) as exc:
        raise AnchorError(f"failed to record anchor: {exc}") from exc
    return receipt, anchor_id, event_seq


def record_backup_verification(
    conn: sqlite3.Connection,
    verifier: OffMachineBackupVerifier,
    request: BackupVerificationRequest,
    *,
    backup_root: str | Path,
) -> tuple[BackupVerificationReceipt, str, int]:
    """Verify under backup_root then append-only record.

    Returns ``(receipt, backup_id, registration_event_seq)``.
    """
    rl = str(request.research_lineage_id).strip()
    if not rl:
        raise BackupVerificationError("research_lineage_id required")
    if int(request.final_event_seq) < 1:
        raise BackupVerificationError("final_event_seq must be >= 1")
    tip_hash = str(request.final_event_hash).strip().lower()
    if len(tip_hash) != 64:
        raise BackupVerificationError("final_event_hash must be SHA-256 hex")
    snap_hash = str(request.expected_snapshot_sha256).strip().lower()
    if len(snap_hash) != 64:
        raise BackupVerificationError("expected_snapshot_sha256 must be SHA-256 hex")
    normalized = BackupVerificationRequest(
        research_lineage_id=rl,
        snapshot_relative_path=str(request.snapshot_relative_path).strip(),
        expected_snapshot_sha256=snap_hash,
        expected_size_bytes=int(request.expected_size_bytes),
        final_event_seq=int(request.final_event_seq),
        final_event_hash=tip_hash,
    )
    if normalized.expected_size_bytes < 0:
        raise BackupVerificationError("expected_size_bytes must be >= 0")

    receipt = verifier.verify(normalized, backup_root=Path(backup_root))
    if not isinstance(receipt.status, BackupStatus):
        raise BackupVerificationError("verifier returned invalid status")
    if receipt.provider_id != verifier.provider_id:
        raise BackupVerificationError("provider_id mismatch on receipt")

    backup_id = require_safe_path_component(_new_id("bak"), field="backup_id")
    payload = {
        "backup_id": backup_id,
        "provider_id": receipt.provider_id,
        "status": receipt.status.value,
        "research_lineage_id": normalized.research_lineage_id,
        "snapshot_relative_path": normalized.snapshot_relative_path,
        "snapshot_sha256": normalized.expected_snapshot_sha256,
        "snapshot_size_bytes": normalized.expected_size_bytes,
        "final_event_seq": normalized.final_event_seq,
        "final_event_hash": normalized.final_event_hash,
        "verified_at": receipt.verified_at,
        "detail": dict(receipt.detail),
    }
    try:
        event_seq, _event_hash = append_event(
            conn,
            event_type="off_machine_backup_recorded",
            payload=payload,
        )
        conn.execute(
            """
            INSERT INTO off_machine_backups(
                backup_id, provider_id, status, research_lineage_id,
                snapshot_relative_path, snapshot_sha256, snapshot_size_bytes,
                final_event_seq, final_event_hash, registration_event_seq,
                verified_at, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                backup_id,
                receipt.provider_id,
                receipt.status.value,
                normalized.research_lineage_id,
                normalized.snapshot_relative_path,
                normalized.expected_snapshot_sha256,
                normalized.expected_size_bytes,
                normalized.final_event_seq,
                normalized.final_event_hash,
                event_seq,
                receipt.verified_at,
                canonical_json(dict(receipt.detail)),
            ),
        )
    except (sqlite3.Error, LedgerHashError) as exc:
        raise BackupVerificationError(
            f"failed to record backup verification: {exc}"
        ) from exc
    return receipt, backup_id, event_seq


def latest_anchor_status(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    final_event_seq: int,
) -> Optional[AnchorStatus]:
    """Latest recorded status for tip, or None if no row."""
    row = conn.execute(
        """
        SELECT status FROM external_anchors
        WHERE research_lineage_id = ?
          AND final_event_seq = ?
        ORDER BY registration_event_seq DESC
        LIMIT 1
        """,
        (str(research_lineage_id).strip(), int(final_event_seq)),
    ).fetchone()
    if row is None:
        return None
    return AnchorStatus(str(row[0]))


def latest_backup_status(
    conn: sqlite3.Connection,
    *,
    research_lineage_id: str,
    final_event_seq: int,
) -> Optional[BackupStatus]:
    """Latest recorded backup status for tip, or None if no row."""
    row = conn.execute(
        """
        SELECT status FROM off_machine_backups
        WHERE research_lineage_id = ?
          AND final_event_seq = ?
        ORDER BY registration_event_seq DESC
        LIMIT 1
        """,
        (str(research_lineage_id).strip(), int(final_event_seq)),
    ).fetchone()
    if row is None:
        return None
    return BackupStatus(str(row[0]))
