"""PR5 promotion blocks: unanchored / unverified backup cannot promote."""

from __future__ import annotations

import hashlib
from pathlib import Path

from crl.db.schema import connect_p1, migrate_database
from crl.research.anchor.local_backup import LocalPathBackupVerifier
from crl.research.anchor.null_provider import NullAnchorProvider
from crl.research.anchor.service import record_anchor, record_backup_verification
from crl.research.anchor.types import (
    AnchorStatus,
    AnchorTarget,
    BackupVerificationRequest,
)
from crl.research.ledger.completeness import assess_completeness
from crl.research.ledger.events import append_event
from crl.research.programme.models import GovernanceCompleteness

HASH_A = "a" * 64
T0 = "2020-01-01T00:00:00.000000Z"


def _seed(db: Path):
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
    append_event(
        conn,
        event_type="legacy_n_bound_proposed",
        payload={"n": 1},
    )
    conn.execute("COMMIT")
    return conn


def test_null_providers_block_promotion(tmp_path: Path):
    conn = _seed(tmp_path / "t.sqlite")
    try:
        tip = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])
        conn.execute("BEGIN")
        record_anchor(
            conn,
            NullAnchorProvider(),
            AnchorTarget(
                research_lineage_id="rl1",
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
        )
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")
        assert a.promotion_blocked is True
        assert "missing_external_anchor_pr5" in a.gaps
        assert "missing_verified_off_machine_backup_pr5" in a.gaps
        assert a.completeness is not GovernanceCompleteness.COMPLETE
    finally:
        conn.close()


def test_verified_backup_alone_still_blocks_without_anchor(tmp_path: Path):
    db = tmp_path / "t.sqlite"
    backup_root = tmp_path / "b"
    backup_root.mkdir()
    data = b"snap"
    (backup_root / "s.db").write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    conn = _seed(db)
    try:
        tip = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])
        conn.execute("BEGIN")
        record_backup_verification(
            conn,
            LocalPathBackupVerifier(),
            BackupVerificationRequest(
                research_lineage_id="rl1",
                snapshot_relative_path="s.db",
                expected_snapshot_sha256=digest,
                expected_size_bytes=len(data),
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
            backup_root=backup_root,
        )
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")
        assert a.promotion_blocked is True
        assert "missing_external_anchor_pr5" in a.gaps
        # backup gap should clear for this tip
        assert "missing_verified_off_machine_backup_pr5" not in a.gaps
    finally:
        conn.close()


def test_fake_anchored_provider_clears_anchor_gap_not_complete(tmp_path: Path):
    from datetime import datetime, timezone

    from crl.research.anchor.types import AnchorReceipt

    class AlwaysAnchored:
        provider_id = "test_anchor"

        def anchor(self, target):
            dt = datetime.now(timezone.utc)
            return AnchorReceipt(
                status=AnchorStatus.ANCHORED,
                provider_id=self.provider_id,
                target=target,
                external_ref="opaque-ref",
                attested_at=dt.strftime("%Y-%m-%dT%H:%M:%S.")
                + f"{dt.microsecond:06d}Z",
                detail={},
            )

    conn = _seed(tmp_path / "t.sqlite")
    try:
        tip = conn.execute(
            "SELECT MAX(event_seq), event_hash FROM ledger_events"
        ).fetchone()
        seq, tip_hash = int(tip[0]), str(tip[1])
        conn.execute("BEGIN")
        record_anchor(
            conn,
            AlwaysAnchored(),
            AnchorTarget(
                research_lineage_id="rl1",
                final_event_seq=seq,
                final_event_hash=tip_hash,
            ),
        )
        conn.execute("COMMIT")
        a = assess_completeness(conn, research_lineage_id="rl1")
        assert a.promotion_blocked is True
        assert "missing_external_anchor_pr5" not in a.gaps
        assert "missing_verified_off_machine_backup_pr5" in a.gaps
        assert a.completeness is not GovernanceCompleteness.COMPLETE
    finally:
        conn.close()
