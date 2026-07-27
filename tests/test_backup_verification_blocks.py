"""PR5 backup verification edge cases."""

from __future__ import annotations

import hashlib
from pathlib import Path

from crl.db.schema import connect_p1, migrate_database
from crl.research.anchor.local_backup import LocalPathBackupVerifier
from crl.research.anchor.null_provider import NullBackupVerifier
from crl.research.anchor.service import record_backup_verification
from crl.research.anchor.types import BackupStatus, BackupVerificationRequest
from crl.research.ledger.completeness import assess_completeness
from crl.research.ledger.events import append_event

T0 = "2020-01-01T00:00:00.000000Z"
HASH_A = "a" * 64


def test_unverified_backup_blocks_promotion(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    migrate_database(db)
    conn = connect_p1(db)
    try:
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, created_at, description)
            VALUES ('rl1', ?, 't')
            """,
            (T0,),
        )
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 1})
        tip = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])
        record_backup_verification(
            conn,
            NullBackupVerifier(),
            BackupVerificationRequest(
                research_lineage_id="rl1",
                snapshot_relative_path="x.db",
                expected_snapshot_sha256=HASH_A,
                expected_size_bytes=0,
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
            backup_root=tmp_path,
        )
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")
        assert a.promotion_blocked is True
        assert "missing_verified_off_machine_backup_pr5" in a.gaps
    finally:
        conn.close()


def test_tip_n_backup_does_not_cover_tip_n_plus_k(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    backup_root = tmp_path / "b"
    backup_root.mkdir()
    data = b"one"
    (backup_root / "s.db").write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    migrate_database(db)
    conn = connect_p1(db)
    try:
        conn.execute("BEGIN")
        conn.execute(
            """
            INSERT INTO research_lineages(research_lineage_id, created_at, description)
            VALUES ('rl1', ?, 't')
            """,
            (T0,),
        )
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 1})
        tip1 = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq1, hash1 = int(tip1[0]), str(tip1[1])
        record_backup_verification(
            conn,
            LocalPathBackupVerifier(),
            BackupVerificationRequest(
                research_lineage_id="rl1",
                snapshot_relative_path="s.db",
                expected_snapshot_sha256=digest,
                expected_size_bytes=len(data),
                final_event_seq=seq1,
                final_event_hash=hash1,
            ),
            backup_root=backup_root,
        )
        # Advance tip without new backup.
        append_event(conn, event_type="legacy_n_bound_proposed", payload={"n": 2})
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")
        # Assessed tip is now N+1; backup for N must not clear gap.
        assert "missing_verified_off_machine_backup_pr5" in a.gaps
        assert a.promotion_blocked is True
    finally:
        conn.close()
