"""PR5 append-only anchor/backup recording + immutability."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from crl.db.schema import connect_p1, migrate_database
from crl.research.anchor.local_backup import LocalPathBackupVerifier
from crl.research.anchor.null_provider import NullAnchorProvider
from crl.research.anchor.service import (
    latest_anchor_status,
    latest_backup_status,
    record_anchor,
    record_backup_verification,
)
from crl.research.anchor.types import (
    AnchorStatus,
    AnchorTarget,
    BackupStatus,
    BackupVerificationRequest,
)
HASH_A = "a" * 64
HASH_B = "b" * 64
T0 = "2020-01-01T00:00:00.000000Z"


def _seed(db: Path) -> sqlite3.Connection:
    migrate_database(db)
    conn = connect_p1(db)
    conn.execute("BEGIN")
    conn.execute(
        """
        INSERT INTO research_lineages(research_lineage_id, created_at, description)
        VALUES ('rl1', ?, 't')
        """,
        (T0,),
    )
    # Minimal tip event so FKs / tip lookups work.
    from crl.research.ledger.events import append_event

    append_event(
        conn,
        event_type="legacy_n_bound_proposed",
        payload={"n": 1, "note": "fixture"},
    )
    conn.execute("COMMIT")
    return conn


def test_null_anchor_append_only_and_immutable(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    conn = _seed(db)
    try:
        tip = conn.execute("SELECT MAX(event_seq), event_hash FROM ledger_events").fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])
        conn.execute("BEGIN")
        receipt, anchor_id, eseq = record_anchor(
            conn,
            NullAnchorProvider(),
            AnchorTarget(
                research_lineage_id="rl1",
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
        )
        conn.execute("COMMIT")
        assert receipt.status is AnchorStatus.UNANCHORED_PENDING
        assert latest_anchor_status(
            conn, research_lineage_id="rl1", final_event_seq=seq
        ) is AnchorStatus.UNANCHORED_PENDING
        n_events = conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
        assert int(n_events) >= 2
        row = conn.execute(
            "SELECT status FROM external_anchors WHERE anchor_id=?",
            (anchor_id,),
        ).fetchone()
        assert row[0] == "UNANCHORED_PENDING"
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE external_anchors SET status='ANCHORED' WHERE anchor_id=?",
                (anchor_id,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "DELETE FROM external_anchors WHERE anchor_id=?",
                (anchor_id,),
            )
        # prior event rows unchanged length for first event
        first = conn.execute(
            "SELECT event_type FROM ledger_events WHERE event_seq=1"
        ).fetchone()[0]
        assert first == "legacy_n_bound_proposed"
        _ = eseq
    finally:
        conn.close()


def test_later_anchor_is_new_row_not_mutation(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    conn = _seed(db)
    try:
        tip = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])

        class FakeAnchor:
            provider_id = "fake"

            def __init__(self) -> None:
                self._n = 0

            def anchor(self, target):
                from crl.research.anchor.types import AnchorReceipt
                from datetime import datetime, timezone

                self._n += 1
                status = (
                    AnchorStatus.UNANCHORED_PENDING
                    if self._n == 1
                    else AnchorStatus.ANCHORED
                )
                dt = datetime.now(timezone.utc)
                return AnchorReceipt(
                    status=status,
                    provider_id=self.provider_id,
                    target=target,
                    external_ref="ref1" if status is AnchorStatus.ANCHORED else None,
                    attested_at=dt.strftime("%Y-%m-%dT%H:%M:%S.")
                    + f"{dt.microsecond:06d}Z",
                    detail={"n": self._n},
                )

        provider = FakeAnchor()
        conn.execute("BEGIN")
        r1, id1, _ = record_anchor(
            conn,
            provider,
            AnchorTarget(
                research_lineage_id="rl1",
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
        )
        r2, id2, _ = record_anchor(
            conn,
            provider,
            AnchorTarget(
                research_lineage_id="rl1",
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
        )
        conn.execute("COMMIT")
        assert r1.status is AnchorStatus.UNANCHORED_PENDING
        assert r2.status is AnchorStatus.ANCHORED
        assert id1 != id2
        n = conn.execute("SELECT COUNT(*) FROM external_anchors").fetchone()[0]
        assert int(n) == 2
        # first row still pending
        st1 = conn.execute(
            "SELECT status FROM external_anchors WHERE anchor_id=?", (id1,)
        ).fetchone()[0]
        assert st1 == "UNANCHORED_PENDING"
        assert latest_anchor_status(
            conn, research_lineage_id="rl1", final_event_seq=seq
        ) is AnchorStatus.ANCHORED
    finally:
        conn.close()


def test_local_backup_record_verified(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    backup_root = tmp_path / "backup"
    backup_root.mkdir()
    data = b"consistent-snapshot"
    snap = backup_root / "snap.db"
    snap.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    conn = _seed(db)
    try:
        tip = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])
        conn.execute("BEGIN")
        receipt, backup_id, _ = record_backup_verification(
            conn,
            LocalPathBackupVerifier(),
            BackupVerificationRequest(
                research_lineage_id="rl1",
                snapshot_relative_path="snap.db",
                expected_snapshot_sha256=digest,
                expected_size_bytes=len(data),
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
            backup_root=backup_root,
        )
        conn.execute("COMMIT")
        assert receipt.status is BackupStatus.BACKUP_VERIFIED
        assert latest_backup_status(
            conn, research_lineage_id="rl1", final_event_seq=seq
        ) is BackupStatus.BACKUP_VERIFIED
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "DELETE FROM off_machine_backups WHERE backup_id=?",
                (backup_id,),
            )
    finally:
        conn.close()
