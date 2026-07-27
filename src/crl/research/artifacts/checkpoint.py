"""Post-event local checkpoints (non-authoritative for promotion).

Capture order avoids circularity:
1. Serialize against writers (BEGIN IMMEDIATE).
2. Read committed ledger tip (pre-checkpoint).
3. Create consistent backup snapshot containing exactly that tip.
4. Hash snapshot; aggregate sealed artefact identities at/before the tip.
5. Append checkpoint event + row after that tip.
Failure leaves no checkpoint row/event. Orphan snapshots are non-authoritative.
Local checkpoints always have is_authoritative=0 (no PR5 authority).
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from crl.db.schema import connect_p1, get_schema_version
from crl.db.snapshot import SnapshotError, create_consistent_snapshot
from crl.research.artifacts.code_identity import CodeIdentity, derive_code_identity
from crl.research.artifacts.merkle import aggregate_digest_merkle, empty_merkle_root
from crl.research.artifacts.paths import (
    ArtifactPathError,
    require_artifact_root,
    require_safe_path_component,
    resolve_under_root,
)
from crl.research.ledger.events import append_event, _utc_text
from crl.research.ledger.hash_chain import GENESIS_PREV_EVENT_HASH


class CheckpointError(RuntimeError):
    """Checkpoint capture failed (transaction rolled back)."""


@dataclass(frozen=True)
class CheckpointResult:
    checkpoint_id: str
    checkpoint_event_seq: int
    checkpoint_event_hash: str
    final_event_seq: int
    final_event_hash: str
    database_snapshot_hash: str
    artifact_aggregate_merkle_root: str
    snapshot_path: Path
    is_authoritative: bool
    is_local_only: bool
    code_identity: CodeIdentity


def _tip(conn: sqlite3.Connection) -> tuple[int, str]:
    row = conn.execute(
        """
        SELECT event_seq, event_hash
        FROM ledger_events
        ORDER BY event_seq DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return 0, GENESIS_PREV_EVENT_HASH
    return int(row[0]), str(row[1])


def _aggregate_artifacts_at_or_before(
    conn: sqlite3.Connection, final_event_seq: int
) -> str:
    rows = conn.execute(
        """
        SELECT artifact_id, merkle_root
        FROM artifact_digests
        WHERE registration_event_seq <= ?
        ORDER BY artifact_id ASC
        """,
        (int(final_event_seq),),
    ).fetchall()
    items = [(str(r[0]), str(r[1])) for r in rows]
    if not items:
        return empty_merkle_root()
    return aggregate_digest_merkle(items)


def create_post_event_checkpoint(
    database_path: str | Path,
    *,
    artifact_root: str | Path,
    checkpoint_id: Optional[str] = None,
    recorded_at: Optional[datetime] = None,
    _inject_failure: Optional[str] = None,
    _race_hook=None,
) -> CheckpointResult:
    """Create a local post-event checkpoint (never authoritative for promotion)."""
    db_path = Path(database_path).resolve()
    root = require_artifact_root(artifact_root)
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise CheckpointError("artifact_root must not be a symlink")
    snap_dir = root / "artifacts" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    if snap_dir.is_symlink():
        raise CheckpointError("snapshot directory must not be a symlink")

    # System-derived only — ignore any caller identity claims.
    code = derive_code_identity()
    try:
        cid = require_safe_path_component(
            (checkpoint_id or f"ckpt_{uuid.uuid4().hex}").strip(),
            field="checkpoint_id",
        )
    except ArtifactPathError as exc:
        raise CheckpointError(str(exc)) from exc

    rel_snap = f"artifacts/snapshots/checkpoint_{cid}.sqlite"
    try:
        snapshot_path = resolve_under_root(root, rel_snap)
    except ArtifactPathError as exc:
        raise CheckpointError(str(exc)) from exc

    conn = connect_p1(db_path)
    conn.isolation_level = None
    error: BaseException | None = None
    created_snapshot = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        version = get_schema_version(conn)
        if version is None or int(version) < 4:
            raise CheckpointError("checkpoints require schema v4")

        final_seq, final_hash = _tip(conn)
        if snapshot_path.exists() or snapshot_path.is_symlink():
            raise CheckpointError(
                f"checkpoint snapshot destination exists: {snapshot_path}"
            )

        # Release the write lock only after we have the tip; the backup API
        # captures a consistent view. Re-take IMMEDIATE before append so the
        # tip cannot move without our noticing.
        conn.execute("COMMIT")

        meta = create_consistent_snapshot(
            db_path,
            snapshot_path,
            expected_tip_seq=final_seq,
            expected_tip_hash=final_hash,
            _race_hook=_race_hook,
        )
        created_snapshot = True
        if meta.method != "sqlite_backup":
            raise CheckpointError("snapshot method must be sqlite_backup")

        if _inject_failure == "after_snapshot":
            raise CheckpointError("injected failure after snapshot")

        # Re-lock writers and confirm tip unchanged before appending checkpoint.
        conn.execute("BEGIN IMMEDIATE")
        tip2_seq, tip2_hash = _tip(conn)
        if tip2_seq != final_seq or tip2_hash != final_hash:
            raise CheckpointError(
                "ledger tip moved during checkpoint snapshot; retry required"
            )

        aggregate = _aggregate_artifacts_at_or_before(conn, final_seq)
        event_seq, event_hash = append_event(
            conn,
            event_type="checkpoint_recorded",
            payload={
                "checkpoint_id": cid,
                "final_event_seq": final_seq,
                "final_event_hash": final_hash,
                "database_snapshot_hash": meta.sha256,
                "artifact_aggregate_merkle_root": aggregate,
                "snapshot_relative_path": rel_snap,
                "snapshot_byte_size": meta.byte_size,
                "code_git_sha": code.git_sha,
                "code_package_version": code.package_version,
                "code_dirty": bool(code.dirty),
                "is_local_only": True,
                "is_authoritative": False,
            },
            recorded_at=recorded_at,
        )
        if event_seq != final_seq + 1:
            raise CheckpointError(
                f"checkpoint event_seq {event_seq} != final_event_seq+1 "
                f"({final_seq + 1})"
            )
        if _inject_failure == "after_event":
            raise CheckpointError("injected failure after checkpoint event")

        conn.execute(
            """
            INSERT INTO checkpoints(
                checkpoint_id, checkpoint_event_seq, final_event_seq,
                final_event_hash, database_snapshot_hash,
                artifact_aggregate_merkle_root, snapshot_byte_size,
                snapshot_relative_path, recorded_at, code_git_sha,
                code_package_version, code_dirty, is_local_only,
                is_authoritative
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (
                cid,
                event_seq,
                final_seq,
                final_hash,
                meta.sha256,
                aggregate,
                meta.byte_size,
                rel_snap,
                _utc_text(recorded_at),
                code.git_sha,
                code.package_version,
                1 if code.dirty else 0,
            ),
        )
        if _inject_failure == "before_commit":
            raise CheckpointError("injected failure before checkpoint commit")

        return CheckpointResult(
            checkpoint_id=cid,
            checkpoint_event_seq=event_seq,
            checkpoint_event_hash=event_hash,
            final_event_seq=final_seq,
            final_event_hash=final_hash,
            database_snapshot_hash=meta.sha256,
            artifact_aggregate_merkle_root=aggregate,
            snapshot_path=snapshot_path,
            is_authoritative=False,
            is_local_only=True,
            code_identity=code,
        )
    except (SnapshotError, CheckpointError) as exc:
        error = exc
        if not isinstance(exc, CheckpointError):
            raise CheckpointError(str(exc)) from exc
        raise
    except BaseException as exc:
        error = exc
        raise
    finally:
        if error is None:
            try:
                conn.execute("COMMIT")
            except sqlite3.Error:
                pass
        else:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            # Orphan snapshot created by this failed call may be removed.
            if created_snapshot and snapshot_path is not None and snapshot_path.exists():
                try:
                    snapshot_path.resolve().relative_to(root.resolve())
                    snapshot_path.unlink()
                except Exception:
                    pass
        conn.close()
